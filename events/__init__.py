"""Events module: "Who's going?" + event recommendations (Member 3).

The backend calls these (team contract):
    events.checkin(student_id, event_id)
    events.attendees(event_id, viewer_id)
    events.recommend_events(student_id, k=5)
Extra:
    events.going_together(student_id, event_id, k=3)
"""
from .checkins import attendees, checkin
from .going_together import going_together
from .recommend import recommend_events

__all__ = ["checkin", "attendees", "recommend_events", "going_together"]
