"""
The "going together" hint shown on an event page.

    going_together(student_id, event_id, k=3)
    -> {"event_id", "going_count", "shares_skills_count", "suggested": [...],
        "message", "source"}

Example message: "3 students from your college are going; 1 shares your skills."

PRIVACY: we start from attendees(), which already hides opted-out and ghost-mode
students. Whatever Member 1's matching returns is then filtered against that
list, so a hidden student can never come back in through the matching module.

DEPENDENCY: suggestions come from Member 1's
    matching.recommend_teammates(student_id, event_id=event_id, k=k)
Until that function exists (or if it fails), a simple local fallback is used:
it prefers attendees who bring skills you do not have. "source" in the result
says which one was used.
"""
from .checkins import get_store


def _same_college(viewer, other):
    """If profiles have a "college" field, only count people from your college.
    The shared contract has no such field yet, so by default everyone counts."""
    vc, oc = viewer.get("college"), other.get("college")
    return vc is None or oc is None or vc == oc


def _fallback_teammates(viewer, candidates, k):
    mine = {s.lower() for s in viewer.get("skills", [])}
    scored = []
    for p in candidates:
        theirs = {s.lower() for s in p.get("skills", [])}
        new, shared = sorted(theirs - mine), sorted(theirs & mine)
        score = (len(new) + 0.5 * len(shared)) / max(len(theirs), 1)
        if new:
            reason = f"Brings skills you don't have: {', '.join(new)}"
        elif shared:
            reason = f"Shares your skills: {', '.join(shared)}"
        else:
            reason = "Going to the same event"
        scored.append({"student_id": p["id"], "score": round(min(score, 1.0), 3),
                       "roles_covered": new, "reason": reason})
    scored.sort(key=lambda r: (-r["score"], r["student_id"]))
    return scored[:k]


def _from_matching(student_id, event_id, k):
    """Ask Member 1's module. Returns None if it is not available yet."""
    try:
        import matching
        fn = getattr(matching, "recommend_teammates", None)
        if fn is None:
            return None
        return list(fn(student_id, event_id=event_id, k=k * 5))  # ask for extra, we filter
    except Exception:
        return None


def going_together(student_id, event_id, k=3, store=None):
    store = store or get_store()
    viewer = store.students[student_id] if student_id in store.students else None
    if viewer is None:
        raise ValueError(f"Unknown student: {student_id}")

    visible = store.attendees(event_id, student_id)               # privacy-safe list
    profiles = [store.students[r["student_id"]] for r in visible]
    profiles = [p for p in profiles if _same_college(viewer, p)]
    allowed = {p["id"]: p for p in profiles}

    mine = {s.lower() for s in viewer.get("skills", [])}
    shares = sum(1 for p in profiles if mine & {s.lower() for s in p.get("skills", [])})

    suggestions = _from_matching(student_id, event_id, k)
    source = "matching"
    if suggestions is None:
        suggestions, source = _fallback_teammates(viewer, profiles, k), "fallback"
    else:
        # keep only people who are going AND visible, in matching's order
        suggestions = [s for s in suggestions if s.get("student_id") in allowed][:k]

    suggested = [{"student_id": s["student_id"], "name": allowed[s["student_id"]]["name"],
                  "score": s.get("score"), "roles_covered": s.get("roles_covered", []),
                  "reason": s.get("reason", "")} for s in suggestions]

    n = len(profiles)
    if n == 0:
        message = "No one from your college has shared that they are going yet."
    else:
        people = "student" if n == 1 else "students"
        verb = "is" if n == 1 else "are"
        message = f"{n} {people} from your college {verb} going; {shares} share{'s' if shares == 1 else ''} your skills."
    return {"event_id": event_id, "going_count": n, "shares_skills_count": shares,
            "suggested": suggested, "message": message, "source": source}
