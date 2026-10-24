"""Events module: "Who's going?" + event recommendations (Member 3).

The backend calls these exactly as in the team contract:
    events.checkin(student_id, event_id)
    events.attendees(event_id, viewer_id)
"""
from .checkins import attendees, checkin

__all__ = ["checkin", "attendees"]
