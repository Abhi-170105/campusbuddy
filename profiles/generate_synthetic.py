import json
import random
from pathlib import Path
import pandas as pd

from profiles.schema import VALID_ROLES, validate_profile_dict
from profiles.taxonomy import normalize_skills


BRANCHES = ["CSE", "ECE", "EEE", "ISE", "MECH"]
YEARS = [1, 2, 3, 4]
SKILL_POOL = [
    "python", "ml", "machine learning", "dl", "nlp", "cv",
    "react", "javascript", "typescript", "ui/ux design", "figma",
    "node.js", "fastapi", "flask", "sql", "docker", "aws", "git",
]
INTEREST_POOL = [
    "hackathons", "nlp", "computer vision", "fintech", "healthtech",
    "clean energy", "robotics", "open source", "cloud systems", "ui craft",
]
GOAL_POOL = [
    "placements", "research", "internships", "startup", "hackathon wins",
]
AVAILABILITY_POOL = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def generate_profiles(num_profiles: int = 300, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    records: list[dict] = []

    for idx in range(1, num_profiles + 1):
        student_id = f"S{idx:03d}"
        year = rng.choice(YEARS)
        branch = rng.choice(BRANCHES)

        if year >= 3:
            role = rng.choices(["mentor", "both", "mentee"], weights=[0.45, 0.35, 0.20])[0]
        else:
            role = rng.choices(["mentee", "both", "mentor"], weights=[0.70, 0.20, 0.10])[0]

        raw_skills = rng.sample(SKILL_POOL, k=rng.randint(2, 5))
        canon_skills = normalize_skills(raw_skills) or ["python"]
        interests = rng.sample(INTEREST_POOL, k=rng.randint(2, 4))
        goals = rng.sample(GOAL_POOL, k=rng.randint(1, 3))

        weekend_first = ["sat", "sun"] if rng.random() < 0.75 else []
        other_days = [d for d in AVAILABILITY_POOL if d not in weekend_first]
        availability = weekend_first + rng.sample(other_days, k=rng.randint(1, 2))

        profile_obj = validate_profile_dict(
            {
                "id": student_id,
                "name": f"Student_{student_id}",
                "year": year,
                "branch": branch,
                "skills": canon_skills,
                "interests": interests,
                "goals": goals,
                "availability": availability,
                "role": role,
                "visibility": {
                    "share_events": rng.random() < 0.85,
                    "ghost_mode": rng.random() < 0.10,
                },
            }
        )

        d = profile_obj.to_dict()
        records.append(
            {
                "id": d["id"],
                "name": d["name"],
                "year": d["year"],
                "branch": d["branch"],
                "skills": json.dumps(d["skills"]),
                "interests": json.dumps(d["interests"]),
                "goals": json.dumps(d["goals"]),
                "availability": json.dumps(d["availability"]),
                "role": d["role"],
                "share_events": d["visibility"]["share_events"],
                "ghost_mode": d["visibility"]["ghost_mode"],
            }
        )

    return records


def main() -> None:
    out_path = Path("data/profiles/profiles.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_profiles(num_profiles=300, seed=42)
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} profiles to {out_path}")


if __name__ == "__main__":
    main()
