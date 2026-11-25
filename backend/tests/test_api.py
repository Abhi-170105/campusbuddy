import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_and_profile_lifecycle() -> None:
    assert client.get("/health").status_code == 200

    res = client.get("/profiles/S001")
    assert res.status_code == 200
    profile = res.json()
    assert profile["id"] == "S001"


def test_matching_endpoints() -> None:
    tm = client.get("/match/teammates", params={"student_id": "S001", "k": 3})
    assert tm.status_code == 200
    assert len(tm.json()) == 3
    assert {"student_id", "score", "roles_covered", "reason"}.issubset(tm.json()[0].keys())

    mn = client.get("/match/mentors", params={"student_id": "S001", "k": 3})
    assert mn.status_code == 200
    assert len(mn.json()) > 0


def test_events_privacy_enforcement() -> None:
    eid = client.get("/events").json()[0]["event_id"]

    # Anonymous access without viewer_id must be rejected
    anon = client.get(f"/events/{eid}/attendees")
    assert anon.status_code == 422

    try:
        client.post("/profiles", json={
            "id": "S998", "name": "Visible Student", "year": 2, "branch": "CSE",
            "skills": ["python"], "interests": ["ml"], "goals": ["placements"],
            "availability": ["sat"], "role": "mentee",
            "visibility": {"share_events": True, "ghost_mode": False},
        })
        client.post("/profiles", json={
            "id": "S999", "name": "Ghost Student", "year": 2, "branch": "CSE",
            "skills": ["react"], "interests": ["web"], "goals": ["placements"],
            "availability": ["sun"], "role": "mentee",
            "visibility": {"share_events": True, "ghost_mode": True},
        })

        client.post(f"/events/{eid}/checkin", json={"student_id": "S998"})
        client.post(f"/events/{eid}/checkin", json={"student_id": "S999"})

        att = client.get(f"/events/{eid}/attendees", params={"viewer_id": "S001"})
        assert att.status_code == 200
        ids = {a["student_id"] for a in att.json()}
        assert "S998" in ids
        assert "S999" not in ids
    finally:
        # Remove temporary test users so CSV datasets stay clean
        for path, col in [("data/events/attendance.csv", "student_id"), ("data/profiles/profiles.csv", "id")]:
            df = pd.read_csv(path)
            df[~df[col].isin(["S998", "S999"])].to_csv(path, index=False)


def test_lost_item_search_and_assistant() -> None:
    res = client.post("/items/lost", data={"description": "blue steel flask", "k": "3"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    chat = client.post("/assistant/ask", json={"question": "When do exams start?"})
    assert chat.status_code == 200
    assert "answer" in chat.json()
    assert "sources" in chat.json()
