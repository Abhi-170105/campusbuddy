"""
Step 2 tests: check-ins work, and NO opt-out or ghost-mode student can ever leak.

Every test builds its own small store with a temporary file (pytest's tmp_path),
so the real data/events/attendance.csv is never changed by testing.
Run: python -m pytest events/tests
"""
import random

import pytest

from events.checkins import EventStore, is_visible

EVENTS = [{"event_id": "E1", "title": "Hack", "date": "2026-11-01", "type": "hackathon", "tags": ["web"], "venue": "Hall"},
          {"event_id": "E2", "title": "Talk", "date": "2026-11-02", "type": "talk", "tags": ["ml"], "venue": "Lab"}]


def student(sid, share, ghost):
    return {"id": sid, "name": f"Name {sid}", "skills": ["python"],
            "visibility": {"share_events": share, "ghost_mode": ghost}}


def make_store(tmp_path, students):
    return EventStore(attendance_path=tmp_path / "att.csv", students=students, events=EVENTS)


@pytest.fixture
def store(tmp_path):
    students = [
        student("VIS", True, False),      # visible: the ONLY one others may see
        student("OPTOUT", False, False),  # did not opt in
        student("GHOST", True, True),     # opted in but ghost mode on
        student("BOTH", False, True),     # opted out AND ghost
        {"id": "NOVIS", "name": "Name NOVIS"},                       # visibility missing
        student("WEIRD", "yes", False),   # bad value, not a real True
        student("VIEWER", True, False),
    ]
    s = make_store(tmp_path, students)
    for sid in ["VIS", "OPTOUT", "GHOST", "BOTH", "NOVIS", "WEIRD", "VIEWER"]:
        s.checkin(sid, "E1")
    return s


def ids(rows):
    return {r["student_id"] for r in rows}


# ---------- privacy ----------

def test_only_visible_student_is_shown(store):
    assert ids(store.attendees("E1", "VIEWER")) == {"VIS"}


@pytest.mark.parametrize("hidden", ["OPTOUT", "GHOST", "BOTH", "NOVIS", "WEIRD"])
def test_hidden_students_never_shown_to_anyone(store, hidden):
    for viewer in store.students:
        assert hidden not in ids(store.attendees("E1", viewer))


def test_turning_on_ghost_mode_hides_immediately(store):
    assert "VIS" in ids(store.attendees("E1", "VIEWER"))
    store.students["VIS"]["visibility"]["ghost_mode"] = True
    assert "VIS" not in ids(store.attendees("E1", "VIEWER"))


def test_opting_out_later_hides_immediately(store):
    store.students["VIS"]["visibility"]["share_events"] = False
    assert store.attendees("E1", "VIEWER") == []


def test_output_has_no_extra_personal_fields(store):
    for row in store.attendees("E1", "VIEWER"):
        assert set(row) == {"student_id", "name"}


def test_viewer_not_listed_and_other_events_not_mixed(store):
    store.checkin("VIS", "E2")
    assert "VIEWER" not in ids(store.attendees("E1", "VIEWER"))
    assert ids(store.attendees("E2", "VIEWER")) == {"VIS"}


def test_random_fuzz_no_leak_ever(tmp_path):
    """200 random students with random settings and random check-ins.
    For EVERY event and EVERY viewer, nobody hidden may appear."""
    rng = random.Random(0)
    students = [student(f"R{i}", rng.random() < 0.5, rng.random() < 0.3) for i in range(200)]
    s = make_store(tmp_path, students)
    for st in students:
        for ev in ("E1", "E2"):
            if rng.random() < 0.6:
                s.checkin(st["id"], ev)
    for ev in ("E1", "E2"):
        for viewer in s.students:
            for row in s.attendees(ev, viewer):
                assert is_visible(s.students[row["student_id"]]), f"LEAK: {row} to {viewer}"


def test_real_sample_data_has_no_leak():
    """Same check on the real sample data (read-only, no check-ins)."""
    s = EventStore()
    hidden = {sid for sid, p in s.students.items() if not is_visible(p)}
    assert hidden, "sample data should contain hidden students"
    for ev in s.events:
        for viewer in s.students:
            assert not (ids(s.attendees(ev, viewer)) & hidden)


# ---------- check-in behaviour ----------

def test_checkin_twice_is_safe(tmp_path):
    s = make_store(tmp_path, [student("A", True, False)])
    assert s.checkin("A", "E1")["status"] == "checked_in"
    assert s.checkin("A", "E1")["status"] == "already_checked_in"
    lines = (tmp_path / "att.csv").read_text().strip().splitlines()
    assert lines == ["student_id,event_id", "A,E1"]


def test_checkins_are_saved_to_file(tmp_path):
    students = [student("A", True, False), student("B", True, False)]
    make_store(tmp_path, students).checkin("A", "E1")
    reloaded = make_store(tmp_path, students)          # fresh store reads the file
    assert ids(reloaded.attendees("E1", "B")) == {"A"}


def test_unknown_ids_are_rejected(store):
    with pytest.raises(ValueError):
        store.checkin("NOBODY", "E1")
    with pytest.raises(ValueError):
        store.checkin("VIS", "E999")
    with pytest.raises(ValueError):
        store.attendees("E999", "VIEWER")
    with pytest.raises(ValueError):
        store.attendees("E1", "NOBODY")


def test_contract_functions_are_importable():
    import events
    assert callable(events.checkin) and callable(events.attendees)
