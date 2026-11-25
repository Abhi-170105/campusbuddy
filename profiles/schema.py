from dataclasses import dataclass, field
from typing import Any


VALID_ROLES = ("mentee", "mentor", "both")


@dataclass
class StudentProfile:
    id: str
    name: str
    year: int
    branch: str
    skills: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    availability: list[str] = field(default_factory=list)
    role: str = "mentee"
    visibility: dict[str, bool] = field(
        default_factory=lambda: {"share_events": True, "ghost_mode": False}
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "year": self.year,
            "branch": self.branch,
            "skills": list(self.skills),
            "interests": list(self.interests),
            "goals": list(self.goals),
            "availability": list(self.availability),
            "role": self.role,
            "visibility": dict(self.visibility),
        }


def validate_profile_dict(data: dict[str, Any]) -> StudentProfile:
    if not isinstance(data, dict):
        raise ValueError("Profile must be a dictionary.")

    required_keys = [
        "id",
        "name",
        "year",
        "branch",
        "skills",
        "interests",
        "goals",
        "availability",
        "role",
        "visibility",
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"Missing required profile fields: {missing}")

    profile_id = str(data["id"]).strip()
    name = str(data["name"]).strip()
    branch = str(data["branch"]).strip()
    if not profile_id or not name or not branch:
        raise ValueError("Fields 'id', 'name', and 'branch' must be non-empty strings.")

    if isinstance(data["year"], bool) or not isinstance(data["year"], int) or data["year"] < 1:
        raise ValueError("Field 'year' must be a positive integer.")

    role = str(data["role"]).strip()
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Expected one of {VALID_ROLES}.")

    for list_field in ("skills", "interests", "goals", "availability"):
        if not isinstance(data[list_field], list):
            raise ValueError(f"Field '{list_field}' must be a list of strings.")

    vis = data["visibility"]
    if not isinstance(vis, dict):
        raise ValueError("Field 'visibility' must be a dictionary.")
    for bool_key in ("share_events", "ghost_mode"):
        if bool_key not in vis or not isinstance(vis[bool_key], bool):
            raise ValueError(f"Field 'visibility.{bool_key}' must be a boolean.")

    return StudentProfile(
        id=profile_id,
        name=name,
        year=data["year"],
        branch=branch,
        skills=[str(x).strip() for x in data["skills"] if str(x).strip()],
        interests=[str(x).strip() for x in data["interests"] if str(x).strip()],
        goals=[str(x).strip() for x in data["goals"] if str(x).strip()],
        availability=[str(x).strip() for x in data["availability"] if str(x).strip()],
        role=role,
        visibility={"share_events": vis["share_events"], "ghost_mode": vis["ghost_mode"]},
    )
