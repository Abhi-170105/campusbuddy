"""
Step 2: check-ins and the privacy-safe "Who's going?" list.

Two public functions (the team contract):
    checkin(student_id, event_id)   -> mark a student as going to an event
    attendees(event_id, viewer_id)  -> who else is going, ONLY showing students
                                       who allowed it

PRIVACY RULE (the most important thing in this file):
    A student appears in someone else's list only if
        visibility.share_events is True   AND   visibility.ghost_mode is False.
    Anything missing or unclear counts as "hidden" (we "fail closed").

Where is the data?
    Every "going" record is one row in data/events/attendance.csv
    (student_id, event_id). checkin() adds a row; attendees() reads them.
    Profiles are read fresh on every call, so if a student switches on ghost
    mode, they disappear from all lists immediately.
"""
import csv
from pathlib import Path

from .data import DATA, load_events, load_students


def is_visible(profile):
    """True only if this student has clearly allowed others to see them.

    We use `is True` / `is False` on purpose: a missing field, None, or a
    typo like "yes" all count as NOT allowed. Safer to hide by mistake than
    to show by mistake.
    """
    if not profile:
        return False
    vis = profile.get("visibility") or {}
    return vis.get("share_events") is True and vis.get("ghost_mode") is False


class EventStore:
    """Holds events, profiles and check-ins. Tests create their own small store
    with a temporary file, so they never touch the real data."""

    def __init__(self, attendance_path=None, students=None, events=None):
        self.path = Path(attendance_path) if attendance_path else DATA / "attendance.csv"
        self.events = {e["event_id"]: e for e in (events if events is not None else load_events())}
        # A dict (id -> profile). Kept as a reference, so profile changes show up live.
        self.students = {s["id"]: s for s in (students if students is not None else load_students())}
        self.going = set()  # set of (student_id, event_id) pairs
        if self.path.exists():
            with self.path.open(newline="") as f:
                for row in csv.DictReader(f):
                    self.going.add((row["student_id"], row["event_id"]))

    # ---- contract function 1 ----
    def checkin(self, student_id, event_id):
        if student_id not in self.students:
            raise ValueError(f"Unknown student: {student_id}")
        if event_id not in self.events:
            raise ValueError(f"Unknown event: {event_id}")
        if (student_id, event_id) in self.going:
            return {"student_id": student_id, "event_id": event_id, "status": "already_checked_in"}

        self.going.add((student_id, event_id))
        self._append_row(student_id, event_id)
        return {"student_id": student_id, "event_id": event_id, "status": "checked_in"}

    # ---- contract function 2 ----
    def attendees(self, event_id, viewer_id):
        if event_id not in self.events:
            raise ValueError(f"Unknown event: {event_id}")
        if viewer_id not in self.students:
            raise ValueError(f"Unknown viewer: {viewer_id}")

        result = []
        for student_id, ev in sorted(self.going):
            if ev != event_id or student_id == viewer_id:
                continue                                  # other event, or the viewer themself
            profile = self.students.get(student_id)
            if not is_visible(profile):
                continue                                  # opted out or ghost mode: never shown
            # Return only what the list needs. No skills, no visibility flags.
            result.append({"student_id": student_id, "name": profile["name"]})
        return result

    def _append_row(self, student_id, event_id):
        new_file = not self.path.exists()
        with self.path.open("a", newline="") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["student_id", "event_id"])
            writer.writerow([student_id, event_id])


# One shared store for the app, created the first time it is needed.
_store = None


def get_store():
    global _store
    if _store is None:
        _store = EventStore()
    return _store


def checkin(student_id, event_id):
    """Contract: events.checkin(student_id, event_id)."""
    return get_store().checkin(student_id, event_id)


def attendees(event_id, viewer_id):
    """Contract: events.attendees(event_id, viewer_id). Respects opt-in and ghost mode."""
    return get_store().attendees(event_id, viewer_id)
