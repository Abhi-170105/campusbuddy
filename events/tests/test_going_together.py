"""Tests for the "going together" hint. Run: python -m pytest events/tests"""
import sys
import types

import pytest

from events.checkins import EventStore
from events.going_together import going_together

EVENTS = [{"event_id": "E1", "title": "Hack", "date": "2026-11-01", "type": "hackathon",
           "tags": ["web"], "venue": "Hall"}]


def st(sid, skills, share=True, ghost=False, **extra):
    return {"id": sid, "name": f"Name {sid}", "skills": skills,
            "visibility": {"share_events": share, "ghost_mode": ghost}, **extra}


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "matching", types.ModuleType("matching"))  # no real matching
    students = [st("ME", ["python"]), st("A", ["python", "react"]), st("B", ["figma"]),
                st("GHOST", ["python"], ghost=True), st("OPTOUT", ["ml"], share=False)]
    s = EventStore(attendance_path=tmp_path / "att.csv", students=students, events=EVENTS)
    for sid in ["ME", "A", "B", "GHOST", "OPTOUT"]:
        s.checkin(sid, "E1")
    return s


def test_counts_only_visible_people(store):
    out = going_together("ME", "E1", store=store)
    assert out["going_count"] == 2                 # A and B; not me, ghost or opt-out
    assert out["shares_skills_count"] == 1         # only A shares python
    assert out["message"] == "2 students from your college are going; 1 shares your skills."


def test_fallback_prefers_new_skills(store):
    out = going_together("ME", "E1", store=store)
    assert out["source"] == "fallback"
    assert [s["student_id"] for s in out["suggested"]] == ["B", "A"]
    assert out["suggested"][0]["roles_covered"] == ["figma"]


def test_hidden_students_filtered_even_if_matching_returns_them(store, monkeypatch):
    fake = types.ModuleType("matching")
    fake.recommend_teammates = lambda sid, event_id=None, k=5: [
        {"student_id": "GHOST", "score": 0.99, "roles_covered": [], "reason": "x"},
        {"student_id": "OPTOUT", "score": 0.98, "roles_covered": [], "reason": "x"},
        {"student_id": "NOT_GOING", "score": 0.97, "roles_covered": [], "reason": "x"},
        {"student_id": "A", "score": 0.5, "roles_covered": ["react"], "reason": "frontend"}]
    monkeypatch.setitem(sys.modules, "matching", fake)
    out = going_together("ME", "E1", store=store)
    assert out["source"] == "matching"
    assert [s["student_id"] for s in out["suggested"]] == ["A"]


def test_broken_matching_falls_back(store, monkeypatch):
    fake = types.ModuleType("matching")
    def boom(*a, **kw):
        raise RuntimeError("not ready")
    fake.recommend_teammates = boom
    monkeypatch.setitem(sys.modules, "matching", fake)
    assert going_together("ME", "E1", store=store)["source"] == "fallback"


def test_college_field_used_when_present(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "matching", types.ModuleType("matching"))
    students = [st("ME", ["python"], college="RVCE"), st("A", ["python"], college="RVCE"),
                st("B", ["python"], college="BMS")]
    s = EventStore(attendance_path=tmp_path / "att.csv", students=students, events=EVENTS)
    for sid in ["ME", "A", "B"]:
        s.checkin(sid, "E1")
    out = going_together("ME", "E1", store=s)
    assert out["going_count"] == 1 and out["message"].startswith("1 student from your college is going")


def test_nobody_going(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "matching", types.ModuleType("matching"))
    s = EventStore(attendance_path=tmp_path / "att.csv", students=[st("ME", [])], events=EVENTS)
    out = going_together("ME", "E1", store=s)
    assert out["going_count"] == 0 and out["suggested"] == []
