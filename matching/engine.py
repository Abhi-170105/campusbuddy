import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from profiles.loader import DEFAULT_PROFILES_CSV, load_profiles
from profiles.schema import StudentProfile
from profiles.taxonomy import infer_roles, normalize_skills


FEEDBACK_PATH = Path("data/profiles/mentor_feedback.json")
MODEL_NAME = "all-MiniLM-L6-v2"


@dataclass(frozen=True)
class _PreparedProfile:
    profile: StudentProfile
    skills: frozenset[str]
    roles: frozenset[str]
    sorted_roles: tuple[str, ...]
    availability: frozenset[str]
    avail_len: int
    goals_lower: frozenset[str]
    interests_lower: frozenset[str]
    branch_lower: str


_MODEL: SentenceTransformer | None = None
_PREPARED_CACHE: tuple[str, float, list[_PreparedProfile], dict[str, int]] | None = None
_EMBEDDING_CACHE: dict[tuple[str, ...], np.ndarray] = {}


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(MODEL_NAME)
    return _MODEL


def _get_prepared_profiles(
    csv_path: str | Path = DEFAULT_PROFILES_CSV,
) -> tuple[list[_PreparedProfile], dict[str, int]]:
    global _PREPARED_CACHE
    path = Path(csv_path)
    mtime = path.stat().st_mtime if path.exists() else -1.0
    key = str(path.resolve())
    if _PREPARED_CACHE is None or _PREPARED_CACHE[0] != key or _PREPARED_CACHE[1] != mtime:
        profiles = load_profiles(path)
        prepared: list[_PreparedProfile] = []
        index_by_id: dict[str, int] = {}
        for idx, p in enumerate(profiles):
            norm_skills = frozenset(normalize_skills(p.skills))
            roles = frozenset(infer_roles(norm_skills))
            avail = frozenset(d.lower() for d in p.availability)
            prepared.append(
                _PreparedProfile(
                    profile=p,
                    skills=norm_skills,
                    roles=roles,
                    sorted_roles=tuple(sorted(roles)),
                    availability=avail,
                    avail_len=len(avail),
                    goals_lower=frozenset(g.lower() for g in p.goals),
                    interests_lower=frozenset(i.lower() for i in p.interests),
                    branch_lower=p.branch.strip().lower(),
                )
            )
            index_by_id[p.id] = idx
        _PREPARED_CACHE = (key, mtime, prepared, index_by_id)
    return _PREPARED_CACHE[2], _PREPARED_CACHE[3]


def _profile_text(prep: _PreparedProfile) -> str:
    p = prep.profile
    skills = ", ".join(sorted(prep.skills))
    interests = ", ".join(p.interests)
    goals = ", ".join(p.goals)
    return f"Branch: {p.branch}. Skills: {skills}. Interests: {interests}. Goals: {goals}."


def _get_normalized_matrix(prepared: list[_PreparedProfile]) -> np.ndarray:
    texts = [_profile_text(item) for item in prepared]
    cache_key = tuple(f"{item.profile.id}:{t}" for item, t in zip(prepared, texts))
    if cache_key not in _EMBEDDING_CACHE:
        model = _get_model()
        emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        _EMBEDDING_CACHE[cache_key] = np.asarray(emb, dtype=np.float32)
    return _EMBEDDING_CACHE[cache_key]


def _build_teammate_reason(
    t_skills: frozenset[str],
    t_roles: frozenset[str],
    t_avail: frozenset[str],
    cand: _PreparedProfile,
    redundancy_penalty: float,
) -> str:
    c_skills = cand.skills
    c_roles = cand.roles
    complementary_roles = sorted(c_roles - t_roles)
    shared_days = sorted(t_avail & cand.availability)

    reason_parts: list[str] = []
    if complementary_roles:
        reason_parts.append(f"covers {', '.join(complementary_roles)}")
    else:
        extra_skills = sorted(c_skills - t_skills)
        if extra_skills:
            reason_parts.append(f"brings {', '.join(extra_skills[:2])}")
        else:
            reason_parts.append("shares complementary project focus")

    if shared_days:
        reason_parts.append(f"both free {', '.join(shared_days[:2])}")
    if redundancy_penalty > 0.6:
        reason_parts.append("some skill overlap")
    return ", ".join(reason_parts)


def recommend_teammates(
    student_id: str,
    event_id: str | None = None,
    k: int = 5,
) -> list[dict[str, Any]]:
    _ = event_id
    if k < 1:
        raise ValueError("Parameter 'k' must be at least 1.")

    prepared, index_by_id = _get_prepared_profiles()
    if student_id not in index_by_id:
        raise KeyError(f"Student ID not found: '{student_id}'")

    target_idx = index_by_id[student_id]
    target = prepared[target_idx]
    matrix = _get_normalized_matrix(prepared)
    sims = np.clip(matrix @ matrix[target_idx], 0.0, 1.0).tolist()

    t_skills = target.skills
    t_roles = target.roles
    t_avail = target.availability
    t_avail_len = target.avail_len

    candidates_scored: list[tuple[float, int, float]] = []
    for idx, cand in enumerate(prepared):
        if idx == target_idx:
            continue

        c_roles = cand.roles
        union_roles_len = len(t_roles | c_roles) or 1
        comp_len = len(c_roles - t_roles)
        role_complementarity = comp_len / union_roles_len

        c_skills = cand.skills
        union_skills_len = len(t_skills | c_skills)
        redundancy_penalty = (len(t_skills & c_skills) / union_skills_len) if union_skills_len else 0.0

        shared_len = len(t_avail & cand.availability)
        avail_score = (shared_len / t_avail_len) if t_avail_len else 0.5

        raw_score = (
            0.40 * sims[idx]
            + 0.30 * role_complementarity
            + 0.15 * avail_score
            - 0.15 * redundancy_penalty
        )
        if raw_score < 0.0:
            raw_score = 0.0
        elif raw_score > 1.0:
            raw_score = 1.0

        candidates_scored.append((raw_score, idx, redundancy_penalty))

    top_items = heapq.nlargest(k, candidates_scored, key=lambda item: item[0])
    results: list[dict[str, Any]] = []
    for raw_score, idx, redundancy_penalty in top_items:
        cand = prepared[idx]
        combined_roles = sorted(t_roles | cand.roles)
        roles_covered = combined_roles if combined_roles else ["general"]
        results.append(
            {
                "student_id": cand.profile.id,
                "score": round(float(raw_score), 4),
                "roles_covered": roles_covered,
                "reason": _build_teammate_reason(
                    t_skills, t_roles, t_avail, cand, redundancy_penalty
                ),
            }
        )
    return results


def _load_feedback(feedback_path: Path = FEEDBACK_PATH) -> dict[str, list[dict[str, Any]]]:
    if not feedback_path.exists():
        return {}
    raw = json.loads(feedback_path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return {str(k): list(v) for k, v in raw.items() if isinstance(v, list)}
    return {}


def record_mentor_feedback(
    mentee_id: str,
    mentor_id: str,
    rating: int | float,
    feedback_path: Path = FEEDBACK_PATH,
) -> dict[str, Any]:
    if isinstance(rating, bool) or not isinstance(rating, (int, float)):
        raise ValueError("Rating must be a number between 1 and 5.")
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5.")

    _, index_by_id = _get_prepared_profiles()
    if mentee_id not in index_by_id:
        raise KeyError(f"Student ID not found: '{mentee_id}'")
    if mentor_id not in index_by_id:
        raise KeyError(f"Student ID not found: '{mentor_id}'")

    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    data = _load_feedback(feedback_path)
    entries = data.setdefault(mentor_id, [])
    entries.append({"mentee_id": mentee_id, "rating": float(rating)})
    feedback_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    ratings = [float(item["rating"]) for item in entries]
    avg_rating = round(sum(ratings) / len(ratings), 3)
    return {
        "mentor_id": mentor_id,
        "count": len(ratings),
        "avg_rating": avg_rating,
    }


def recommend_mentors(
    student_id: str,
    k: int = 5,
    feedback_path: Path = FEEDBACK_PATH,
) -> list[dict[str, Any]]:
    if k < 1:
        raise ValueError("Parameter 'k' must be at least 1.")

    prepared, index_by_id = _get_prepared_profiles()
    if student_id not in index_by_id:
        raise KeyError(f"Student ID not found: '{student_id}'")

    mentee = prepared[index_by_id[student_id]]
    feedback_data = _load_feedback(feedback_path)

    mentee_goals = mentee.goals_lower
    mentee_interests = mentee.interests_lower
    mentee_branch = mentee.branch_lower
    mentee_year = mentee.profile.year

    scored: list[tuple[float, dict[str, Any]]] = []
    for cand in prepared:
        mentor = cand.profile
        if mentor.id == mentee.profile.id or mentor.role not in ("mentor", "both"):
            continue

        same_branch = cand.branch_lower == mentee_branch
        branch_score = 1.0 if same_branch else 0.25

        shared_goals = sorted(mentee_goals & cand.goals_lower)
        shared_interests = sorted(mentee_interests & cand.interests_lower)

        goal_score = (len(shared_goals) / len(mentee_goals)) if mentee_goals else 0.0
        interest_score = (
            len(shared_interests) / len(mentee_interests)
        ) if mentee_interests else 0.0
        seniority_bonus = 0.15 if mentor.year > mentee_year else 0.05

        entries = feedback_data.get(mentor.id, [])
        if entries:
            avg_rating = sum(float(e["rating"]) for e in entries) / len(entries)
            normalized_rating = (avg_rating - 1.0) / 4.0
            feedback_component = normalized_rating
            fairness_penalty = 0.04 * math.log1p(len(entries))
        else:
            avg_rating = None
            feedback_component = 0.5
            fairness_penalty = 0.0

        raw_score = (
            0.35 * branch_score
            + 0.30 * goal_score
            + 0.25 * interest_score
            + seniority_bonus
            + 0.10 * feedback_component
            - fairness_penalty
        )
        score = round(float(max(0.0, min(1.0, raw_score))), 4)

        reasons: list[str] = []
        if same_branch:
            reasons.append(f"same branch ({mentor.branch})")
        if shared_goals:
            reasons.append(f"aligned goals: {', '.join(shared_goals[:2])}")
        if shared_interests:
            reasons.append(f"shared interests: {', '.join(shared_interests[:2])}")
        if avg_rating is not None:
            reasons.append(f"rated {avg_rating:.1f}/5")
        if not reasons:
            reasons.append(f"year {mentor.year} {mentor.branch} mentor")

        scored.append(
            (
                score,
                {
                    "student_id": mentor.id,
                    "score": score,
                    "reason": ", ".join(reasons),
                },
            )
        )

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:k]]
