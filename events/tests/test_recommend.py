"""Step 3 tests: recommend_events() gives sensible, safe recommendations.
Run: python -m pytest events/tests"""
import pytest

from events.checkins import EventStore
from events.recommend import cf_scores, content_scores, popularity_scores, recommend_events


def ev(eid, tags):
    return {"event_id": eid, "title": f"Event {eid}", "date": "2026-11-01",
            "type": "workshop", "tags": tags, "venue": "Hall"}


EVENTS = [ev("E1", ["ml"]), ev("E2", ["nlp"]), ev("E3", ["web"]), ev("E4", ["music"]), ev("E5", ["sports"])]


def st(sid, interests=()):
    return {"id": sid, "name": f"Name {sid}", "interests": list(interests), "skills": [], "goals": [],
            "visibility": {"share_events": True, "ghost_mode": False}}


@pytest.fixture
def store(tmp_path):
    students = [st("A", ["music"]), st("B"), st("C"), st("NEW", ["web"])]
    s = EventStore(attendance_path=tmp_path / "att.csv", students=students, events=EVENTS)
    # A and B behave alike (E1, E2). B also went to E3, so A should be shown E3.
    # C is different (E4 only).
    s.going = {("A", "E1"), ("A", "E2"), ("B", "E1"), ("B", "E2"), ("B", "E3"), ("C", "E4")}
    return s


def ids(recs):
    return [r["event_id"] for r in recs]


def test_cf_finds_what_similar_student_did(store):
    assert ids(recommend_events("A", k=1, store=store)) == ["E3"]


def test_cf_beats_own_interest_when_behaviour_says_otherwise(store):
    # A lists "music" (E4), but A's look-alike went to E3: CF puts E3 first.
    recs = ids(recommend_events("A", k=3, store=store))
    assert recs.index("E3") < recs.index("E4")


def test_never_recommends_events_already_going(store):
    for sid in store.students:
        going = {e for s, e in store.going if s == sid}
        assert not going & set(ids(recommend_events(sid, k=5, store=store)))


def test_cold_start_uses_profile_interests(store):
    recs = recommend_events("NEW", k=2, store=store)
    assert recs[0]["event_id"] == "E3"            # NEW likes web
    assert "web" in recs[0]["reason"]


def test_output_format_and_sorted(store):
    recs = recommend_events("A", k=5, store=store)
    assert len(recs) == 3                          # 5 events minus 2 already going
    for r in recs:
        assert set(r) == {"event_id", "title", "date", "score", "reason"}
        assert 0 <= r["score"] <= 1
    scores = [r["score"] for r in recs]
    assert scores == sorted(scores, reverse=True)


def test_k_limits_results(store):
    assert len(recommend_events("NEW", k=2, store=store)) == 2


def test_recommending_does_not_change_data(store):
    before = set(store.going)
    recommend_events("A", k=5, store=store)
    assert store.going == before


def test_unknown_student_rejected(store):
    with pytest.raises(ValueError):
        recommend_events("NOBODY", store=store)


def test_baseline_scores_are_sensible(store):
    pop = popularity_scores(store)
    assert pop["E1"] == pop["E2"] == 0.5 and pop["E5"] == 0  # 2 of 4 students going
    assert content_scores(store, "NEW")["E3"] == 1.0
    cf, n = cf_scores(store, "NEW")
    assert cf == {} and n == 0                      # no history -> no CF


def test_works_on_real_sample_data():
    s = EventStore()
    for sid in list(s.students)[:20] + ["S065"]:     # includes a new student
        recs = recommend_events(sid, k=5, store=s)
        assert 1 <= len(recs) <= 5


def test_contract_function_importable():
    import events
    assert callable(events.recommend_events)
