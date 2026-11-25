# CampusBuddy - Member 1: Student Profiles & Teammate/Mentor Matching

## Owned Modules & Artifacts
- `profiles/schema.py`: `StudentProfile` dataclass and `validate_profile_dict(...)`.
- `profiles/taxonomy.py`: Skill normalization (`normalize_skill`, `normalize_skills`) and role bucket mapping (`infer_roles`).
- `profiles/generate_synthetic.py`: Generates 300 anonymized synthetic student profiles into `data/profiles/profiles.csv`.
- `profiles/loader.py`: Parses and validates CSV profiles via `load_profiles(...)`.
- `matching/engine.py` & `matching/__init__.py`:
  - `recommend_teammates(student_id, event_id=None, k=5)` using `all-MiniLM-L6-v2` embeddings, availability overlap, role complementarity, and redundancy penalties.
  - `recommend_mentors(student_id, k=5)` using content-based branch/goal/interest alignment, seniority weighting, feedback re-ranking, and popularity-dampening fairness.
  - `record_mentor_feedback(mentee_id, mentor_id, rating)` persisting ratings to `data/profiles/mentor_feedback.json`.
- `matching/baselines.py`: Random, TF-IDF, and rule-based (branch + year) teammate baselines.
- `eval/evaluate_matching.py`: Computes Precision@5, Recall@5, NDCG@5, team role coverage, baseline comparisons, and 300-profile pass latency into `eval/metrics_report.json`.
- `tests/test_matching.py`: Unit tests covering schema, taxonomy, loader, matching, baselines, and feedback persistence.

## Running Tests & Evaluation
- Unit tests: `python -m unittest discover -s tests -v`
- Evaluation: `python -m eval.evaluate_matching`
