import json
from pathlib import Path
import pandas as pd

from profiles.schema import StudentProfile, validate_profile_dict


DEFAULT_PROFILES_CSV = Path("data/profiles/profiles.csv")


def _parse_str_list(value: object, field_name: str) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if pd.isna(value):
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except json.JSONDecodeError:
            pass
        return [part.strip() for part in text.split(",") if part.strip()]
    raise ValueError(f"Cannot parse list field '{field_name}' from value: {value!r}")


def _parse_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes"):
            return True
        if lowered in ("false", "0", "no"):
            return False
    return default


def load_profiles(csv_path: str | Path = DEFAULT_PROFILES_CSV) -> list[StudentProfile]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Profiles CSV not found at: {path}")

    df = pd.read_csv(path)
    profiles: list[StudentProfile] = []

    for _, row in df.iterrows():
        raw_dict = {
            "id": row["id"],
            "name": row["name"],
            "year": int(row["year"]),
            "branch": row["branch"],
            "skills": _parse_str_list(row.get("skills", []), "skills"),
            "interests": _parse_str_list(row.get("interests", []), "interests"),
            "goals": _parse_str_list(row.get("goals", []), "goals"),
            "availability": _parse_str_list(row.get("availability", []), "availability"),
            "role": row["role"],
            "visibility": {
                "share_events": _parse_bool(row.get("share_events", True), True),
                "ghost_mode": _parse_bool(row.get("ghost_mode", False), False),
            },
        }
        profiles.append(validate_profile_dict(raw_dict))

    return profiles
