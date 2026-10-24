# Shared contract

**Repo layout:** `profiles/`, `matching/`, `lostfound/`, `events/`, `assistant/`, `backend/`, `frontend/`, `eval/`, `docs/`, `data/`

**Student profile (JSON):**
```json
{
  "id": "S001", "name": "Asha", "year": 2, "branch": "CSE",
  "skills": ["python", "ml"], "interests": ["nlp", "hackathons"],
  "goals": ["placements", "research"], "availability": ["sat", "sun"],
  "role": "mentee",
  "visibility": {"share_events": true, "ghost_mode": false}
}
```
`role` is `mentee`, `mentor` or `both`.

**Python functions each module must expose (backend calls these):**
- `matching.recommend_teammates(student_id, event_id=None, k=5)` returns `[{"student_id", "score", "roles_covered", "reason"}]`
- `matching.recommend_mentors(student_id, k=5)` returns `[{"student_id", "score", "reason"}]`
- `matching.record_mentor_feedback(mentee_id, mentor_id, rating)` (rating 1 to 5)
- `lostfound.add_found_item(image_path, description, location, date)` returns `item_id`
- `lostfound.search_lost_item(description, image_path=None, k=5)` returns `[{"item_id", "score", "location", "date"}]`
- `events.checkin(student_id, event_id)` and `events.attendees(event_id, viewer_id)` (must respect opt-in and ghost mode)
- `events.recommend_events(student_id, k=5)`
- `assistant.ask(question)` returns `{"answer", "sources": []}`

**REST endpoints (owned by Member 4, wrapping the functions above):**
`POST /profiles`, `GET /profiles/{id}`, `GET /match/teammates`, `GET /match/mentors`, `POST /mentors/feedback`, `POST /items/found`, `POST /items/lost`, `POST /events/{id}/checkin`, `GET /events/{id}/attendees`, `GET /events/recommend`, `POST /assistant/ask`

**Team rules:** one shared GitHub repo; each member works only in their own folders; commit daily; data in `data/` is anonymized (no real names or phone numbers); every module must have a small `README.md` and a `tests/` folder.

**Project summary (for context):** CampusBuddy is an AI platform for college students with five modules: teammate matching, mentor-mentee matching, multimodal lost-and-found, an event "Who's going?" feature, and a campus assistant chatbot. Timeline is 3 weeks (21 days). Targets: Precision@5 at least 25% better than keyword baselines; lost-and-found top-5 accuracy at least 80%; SUS score 70 or above in a pilot with 20 to 30 students.
