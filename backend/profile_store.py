import json
from pathlib import Path
from typing import Any
import pandas as pd

from profiles.loader import DEFAULT_PROFILES_CSV, load_profiles
from profiles.schema import validate_profile_dict


def is_valid_college_email(email: str | None) -> bool:
    """Checks college email domain if provided; allows pilot test accounts."""
    if not email:
        return True
    cleaned = email.strip().lower()
    return "@" in cleaned and (
        cleaned.endswith(".edu")
        or cleaned.endswith(".ac.in")
        or cleaned.endswith(".edu.in")
    )


def get_all_profiles(csv_path: Path = DEFAULT_PROFILES_CSV) -> list[dict[str, Any]]:
    if not csv_path.exists():
        return []
    return [p.to_dict() for p in load_profiles(csv_path)]


def get_profile(student_id: str, csv_path: Path = DEFAULT_PROFILES_CSV) -> dict[str, Any] | None:
    for p in load_profiles(csv_path):
        if p.id == student_id:
            return p.to_dict()
    return None


def upsert_profile(data: dict[str, Any], csv_path: Path = DEFAULT_PROFILES_CSV) -> dict[str, Any]:
    """Validates profile against Member 1's schema, saves to CSV, and syncs Events store."""
    email = data.get("email")
    if email and not is_valid_college_email(email):
        raise ValueError("Please use a valid college email address (.edu / .ac.in / .edu.in).")

    profile_obj = validate_profile_dict(data)
    d = profile_obj.to_dict()

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(
            columns=[
                "id", "name", "year", "branch", "skills", "interests",
                "goals", "availability", "role", "share_events", "ghost_mode",
            ]
        )

    row_record = {
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

    if (df["id"] == d["id"]).any():
        idx = df.index[df["id"] == d["id"]][0]
        for col, val in row_record.items():
            df.at[idx, col] = val
    else:
        df = pd.concat([df, pd.DataFrame([row_record])], ignore_index=True)

    df.to_csv(csv_path, index=False)

    # Sync live with Member 3's EventStore so privacy toggles apply immediately
    try:
        from events.checkins import get_store
        store = get_store()
        store.students[d["id"]] = d
    except Exception:
        pass

    return d


def sync_all_to_event_store(csv_path: Path = DEFAULT_PROFILES_CSV) -> None:
    """Loads all profiles from Member 1's CSV into Member 3's live EventStore."""
    try:
        from events.checkins import get_store
        store = get_store()
        for prof in get_all_profiles(csv_path):
            store.students[prof["id"]] = prof
    except Exception:
        pass
