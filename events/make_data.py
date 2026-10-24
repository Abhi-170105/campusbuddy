"""
Step 1: create sample students and a synthetic attendance history.

Run from the project root:   python -m events.make_data

Inputs : data/events/events.json          (hand-written, edit freely)
Outputs: data/events/sample_students.json (profiles in the team's shared format)
         data/events/attendance.csv       (one row = one student attended one event)

Why synthetic data? We have no real attendance records yet. So we simulate
students who belong to a few "taste groups" (ML fans, web/design fans, hardware
fans, culture fans, placement-focused). Each group prefers certain event tags.
Students only LIST some of their true interests in their profile, just like real
students who fill forms lazily. That gives collaborative filtering (which learns
from behaviour) something to discover that a profile-only method cannot.
"""
import json
import random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "events"

SEED = 42            # fixed seed -> the same data every run (reproducible)
N_STUDENTS = 60      # 60 students with history
N_NEW = 5            # extra "new" students with no history (cold start)

# Each taste group: the tags they really like, and typical skills.
GROUPS = {
    "ml":         {"tags": ["ml", "nlp", "python", "cloud"],   "skills": ["python", "ml", "pandas"]},
    "web_design": {"tags": ["web", "design", "entrepreneurship"], "skills": ["javascript", "react", "figma"]},
    "hardware":   {"tags": ["robotics", "iot", "cloud"],       "skills": ["arduino", "c", "embedded"]},
    "culture":    {"tags": ["music", "dance", "sports"],       "skills": ["communication", "event-management"]},
    "placements": {"tags": ["dsa", "placements", "security"],  "skills": ["java", "dsa", "sql"]},
}
BRANCHES = ["CSE", "ECE", "ISE", "MECH", "AIML"]
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
GOALS = ["placements", "research", "higher-studies", "startup"]


def make_student(i, rng, group):
    true_tags = GROUPS[group]["tags"]
    # Profile lists only 1-2 of the true interests (incomplete on purpose).
    listed = rng.sample(true_tags, k=rng.randint(1, 2))
    share = rng.random() < 0.75          # 75% opt in to sharing events
    ghost = rng.random() < 0.10          # 10% use ghost mode
    return {
        "id": f"S{i:03d}",
        "name": f"Student {i:03d}",       # anonymised, no real names
        "year": rng.randint(1, 4),
        "branch": rng.choice(BRANCHES),
        "skills": rng.sample(GROUPS[group]["skills"], k=2),
        "interests": listed,
        "goals": rng.sample(GOALS, k=1),
        "availability": rng.sample(DAYS, k=2),
        "role": rng.choice(["mentee", "mentor", "both"]),
        "visibility": {"share_events": share, "ghost_mode": ghost},
    }, true_tags


def attend_probability(true_tags, event):
    """Chance a student attends: small base + more for each matching tag."""
    overlap = len(set(true_tags) & set(event["tags"]))
    return min(0.05 + 0.45 * overlap, 0.9)


def main():
    rng = random.Random(SEED)
    events = json.loads((DATA / "events.json").read_text())

    students, rows = [], []
    group_names = list(GROUPS)
    for i in range(1, N_STUDENTS + N_NEW + 1):
        group = group_names[(i - 1) % len(group_names)]
        profile, true_tags = make_student(i, rng, group)
        students.append(profile)
        if i > N_STUDENTS:
            continue  # new students: profile only, no attendance history
        for ev in events:
            if rng.random() < attend_probability(true_tags, ev):
                rows.append({"student_id": profile["id"], "event_id": ev["event_id"]})

    (DATA / "sample_students.json").write_text(json.dumps(students, indent=2))
    pd.DataFrame(rows).to_csv(DATA / "attendance.csv", index=False)
    print(f"{len(events)} events, {len(students)} students, {len(rows)} attendance rows")


if __name__ == "__main__":
    main()
