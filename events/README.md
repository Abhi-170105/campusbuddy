# events/ : "Who's going?" and event recommendations (Member 3)

## Functions the backend calls
| Function | Returns |
|---|---|
| `events.checkin(student_id, event_id)` | `{"student_id", "event_id", "status"}` where status is `checked_in` or `already_checked_in` |
| `events.attendees(event_id, viewer_id)` | `[{"student_id", "name"}]`, never anyone opted out or in ghost mode |
| `events.recommend_events(student_id, k=5)` | `[{"event_id", "title", "date", "score", "reason"}]`, best first |
| `events.going_together(student_id, event_id, k=3)` | `{"event_id", "going_count", "shares_skills_count", "suggested", "message", "source"}` |

Unknown student or event ids raise `ValueError` (the backend should turn that into HTTP 404).

```python
import events
events.checkin("S001", "E002")
events.attendees("E002", viewer_id="S003")
events.recommend_events("S001", k=5)
events.going_together("S001", "E002")["message"]   # "4 students from your college are going; 1 shares your skills."
```

## Files
| File | What it does |
|---|---|
| `data.py` | Loads events, sample students and attendance from `data/events/` |
| `make_data.py` | Rebuilds the synthetic data: `python -m events.make_data` (seed 42, same every time) |
| `checkins.py` | `checkin`, `attendees` and the privacy rule `is_visible()` |
| `recommend.py` | Collaborative filtering, content-based fallback, and the two baselines |
| `going_together.py` | The hint on an event page; calls Member 1's `matching.recommend_teammates` |

## Privacy rule
A student is shown to others only if `visibility.share_events` is exactly `True` AND
`visibility.ghost_mode` is exactly `False`. Anything missing or unclear = hidden ("fail closed").
Profiles are read live, so switching ghost mode on hides the student immediately.
`going_together` filters Member 1's suggestions through the same rule.

## Recommender
- Students with history: user-based collaborative filtering (cosine similarity, 10 nearest students).
- New students: content matching between event tags and the student's interests, skills and goals.
- Events the student already checked in to are never recommended.

## Evaluation
`python -m eval.events.evaluate_events` (or open `eval/events/evaluation.ipynb`).
Add pilot check-ins with `--attendance path/to/file.csv`.

| Method | Hit Rate@5 | Precision@5 |
|---|---|---|
| Collaborative filtering | 0.916 | 0.216 |
| Content-only | 0.894 | 0.214 |
| Popularity-only | 0.568 | 0.128 |

CF beats popularity by 61% on Hit Rate@5. CF and content-only are within one standard deviation,
so we do not claim CF beats content. Data is synthetic (12 events, 65 students).

## Tests
`python -m pytest events/tests`: privacy (including a 200-student random leak test),
check-ins, recommendations, going-together.

## Open questions for the team
1. Should ghost mode also stop a student from viewing attendee lists? (Now it only hides them.)
2. Add a `college` field to the profile? `going_together` already uses it if present.
3. Should ghost-mode students' check-ins be left out of the recommender's learning? Only anonymous percentages are shown today.
