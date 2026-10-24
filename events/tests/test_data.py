"""Step 1 tests: is the event data complete and sensible?  Run: python -m pytest events/tests"""
from datetime import date

from events.data import (REQUIRED_EVENT_FIELDS, attendance_matrix, load_attendance,
                         load_events, load_students)

PROFILE_FIELDS = {"id", "name", "year", "branch", "skills", "interests", "goals",
                  "availability", "role", "visibility"}


def test_at_least_10_events_with_all_fields():
    events = load_events()
    assert len(events) >= 10
    for ev in events:
        assert REQUIRED_EVENT_FIELDS <= ev.keys(), f"{ev.get('event_id')} missing fields"
        assert isinstance(ev["tags"], list) and ev["tags"], "tags must be a non-empty list"
        date.fromisoformat(ev["date"])  # crashes if date is not YYYY-MM-DD


def test_event_ids_are_unique():
    ids = [ev["event_id"] for ev in load_events()]
    assert len(ids) == len(set(ids))


def test_students_follow_shared_contract():
    for s in load_students():
        assert PROFILE_FIELDS <= s.keys()
        assert s["role"] in {"mentee", "mentor", "both"}
        assert set(s["visibility"]) == {"share_events", "ghost_mode"}
        assert not any(ch.isdigit() for ch in s["name"].split()[0]), "use anonymised names"


def test_attendance_only_refers_to_known_students_and_events():
    att = load_attendance()
    assert set(att["student_id"]) <= {s["id"] for s in load_students()}
    assert set(att["event_id"]) <= {e["event_id"] for e in load_events()}
    assert not att.duplicated().any()


def test_data_has_privacy_cases_and_new_students():
    students = load_students()
    att_ids = set(load_attendance()["student_id"])
    assert any(not s["visibility"]["share_events"] for s in students), "need opt-out students to test privacy"
    assert any(s["visibility"]["ghost_mode"] for s in students), "need ghost-mode students to test privacy"
    assert any(s["id"] not in att_ids for s in students), "need new students for cold-start"


def test_matrix_is_zero_one():
    grid = attendance_matrix()
    assert set(grid.values.flatten()) <= {0, 1}
