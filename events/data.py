"""
Small helpers to load the event data. Every other file in events/ uses these,
so if the data location or format changes, we only fix it here.
"""
import json
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data" / "events"

REQUIRED_EVENT_FIELDS = {"event_id", "title", "date", "type", "tags", "venue"}


def load_events():
    """List of event dicts from events.json."""
    return json.loads((DATA / "events.json").read_text())


def load_students():
    """Sample student profiles (same JSON format as the team contract).
    Later we swap this for Member 1's real profiles."""
    return json.loads((DATA / "sample_students.json").read_text())


def load_attendance():
    """Table with columns student_id, event_id (one row per attendance)."""
    return pd.read_csv(DATA / "attendance.csv")


def attendance_matrix(attendance=None):
    """Turn the attendance list into a grid: rows = students, columns = events,
    1 = attended, 0 = did not. This grid is what collaborative filtering uses."""
    if attendance is None:
        attendance = load_attendance()
    grid = pd.crosstab(attendance["student_id"], attendance["event_id"])
    return grid.clip(upper=1)  # in case of duplicate rows, keep it 0/1
