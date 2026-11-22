"""
Step 3: recommend events to a student.

Contract:  events.recommend_events(student_id, k=5)
Returns :  [{"event_id", "title", "date", "score", "reason"}], best first

Three scoring methods live here. Step 4 compares them:
  1. popularity_scores : how many students are going (baseline 1)
  2. content_scores    : how well event tags match the student's profile (baseline 2)
  3. cf_scores         : collaborative filtering, "students who behave like you went here"

recommend_events() uses collaborative filtering when the student has history,
and falls back to content matching for brand-new students (the "cold start").
Events the student is already going to are never recommended.

HOW USER-BASED COLLABORATIVE FILTERING WORKS (viva version):
  - Write each student as a row of 0s and 1s, one column per event (1 = going).
  - Compare two students with cosine similarity: 1 = same events, 0 = nothing shared.
  - Take the 10 most similar students ("neighbours").
  - An event's score = weighted share of neighbours going to it, where closer
    neighbours count more. Score is between 0 and 1.
"""
import numpy as np

N_NEIGHBOURS = 10


def _matrix(store):
    """Build the student x event 0/1 grid from the store's check-ins."""
    student_ids = sorted(store.students)
    event_ids = sorted(store.events)
    s_index = {s: i for i, s in enumerate(student_ids)}
    e_index = {e: j for j, e in enumerate(event_ids)}
    grid = np.zeros((len(student_ids), len(event_ids)))
    for sid, eid in store.going:
        if sid in s_index and eid in e_index:
            grid[s_index[sid], e_index[eid]] = 1
    return grid, student_ids, event_ids


def popularity_scores(store):
    """Baseline 1: share of all students going to each event."""
    grid, _, event_ids = _matrix(store)
    counts = grid.sum(axis=0) / max(len(grid), 1)
    return dict(zip(event_ids, counts))


def _profile_words(profile):
    words = profile.get("interests", []) + profile.get("skills", []) + profile.get("goals", [])
    return {w.lower() for w in words}


def content_scores(store, student_id):
    """Baseline 2: fraction of an event's tags found in the student's
    interests, skills or goals. 1.0 = every tag matches."""
    words = _profile_words(store.students[student_id])
    scores = {}
    for eid, ev in store.events.items():
        tags = {t.lower() for t in ev["tags"]}
        scores[eid] = len(tags & words) / len(tags) if tags else 0.0
    return scores


def cf_scores(store, student_id, n_neighbours=N_NEIGHBOURS):
    """User-based collaborative filtering. Returns ({event_id: score}, neighbour_count).
    Empty scores if the student has no history (cold start)."""
    grid, student_ids, event_ids = _matrix(store)
    if student_id not in student_ids:
        return {}, 0
    me = grid[student_ids.index(student_id)]
    if me.sum() == 0:
        return {}, 0

    # cosine similarity between me and everyone else
    norms = np.linalg.norm(grid, axis=1) * np.linalg.norm(me)
    with np.errstate(divide="ignore", invalid="ignore"):
        sims = np.where(norms > 0, grid @ me / norms, 0.0)
    sims[student_ids.index(student_id)] = 0.0          # not my own neighbour

    neighbours = np.argsort(-sims)[:n_neighbours]
    neighbours = neighbours[sims[neighbours] > 0]       # keep only real look-alikes
    if len(neighbours) == 0:
        return {}, 0

    weights = sims[neighbours]
    scores = weights @ grid[neighbours] / weights.sum()
    return dict(zip(event_ids, scores)), len(neighbours)


def _already_going(store, student_id):
    return {e for s, e in store.going if s == student_id}


def rank_popularity(store, student_id, k=5):
    """Baseline 1 as a ranked list of event_ids (skips events already going)."""
    pop = popularity_scores(store)
    already = _already_going(store, student_id)
    order = sorted((e for e in store.events if e not in already), key=lambda e: (-pop[e], e))
    return order[:k]


def rank_content(store, student_id, k=5):
    """Baseline 2 as a ranked list of event_ids. Popularity only breaks ties."""
    content = content_scores(store, student_id)
    pop = popularity_scores(store)
    already = _already_going(store, student_id)
    order = sorted((e for e in store.events if e not in already),
                   key=lambda e: (-content[e], -pop[e], e))
    return order[:k]


def recommend_events(student_id, k=5, store=None):
    """Contract: events.recommend_events(student_id, k=5)."""
    if store is None:
        from .checkins import get_store
        store = get_store()
    if student_id not in store.students:
        raise ValueError(f"Unknown student: {student_id}")

    already = {e for s, e in store.going if s == student_id}
    content = content_scores(store, student_id)
    popular = popularity_scores(store)
    cf, n_nb = cf_scores(store, student_id)
    use_cf = any(cf.get(e, 0) > 0 for e in store.events if e not in already)

    ranked = []
    for eid, ev in store.events.items():
        if eid in already:
            continue
        matched = sorted({t.lower() for t in ev["tags"]} & _profile_words(store.students[student_id]))
        interest_reason = (f"Matches your interests: {', '.join(matched)}" if matched
                           else "Popular on campus")
        if use_cf:
            score = cf.get(eid, 0.0)
            # content and popularity only break ties; CF decides the order
            sort_key = (score, content[eid], popular.get(eid, 0))
            reason = (f"{round(score * 100)}% of the {n_nb} students most like you are going"
                      if score > 0 else interest_reason)
        else:
            score = content[eid]
            sort_key = (score, popular.get(eid, 0))
            reason = interest_reason
        ranked.append((sort_key, eid, round(float(score), 3), reason))

    # highest score first; on a full tie, lower event_id first (same rule as the baselines)
    ranked.sort(key=lambda r: (tuple(-x for x in r[0]), r[1]))
    return [{"event_id": eid, "title": store.events[eid]["title"], "date": store.events[eid]["date"],
             "score": score, "reason": reason}
            for _, eid, score, reason in ranked[:k]]
