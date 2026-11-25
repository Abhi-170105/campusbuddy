import random
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from profiles.loader import load_profiles
from profiles.schema import StudentProfile
from profiles.taxonomy import infer_roles, normalize_skills


def _find_student(profiles: list[StudentProfile], student_id: str) -> StudentProfile:
    for p in profiles:
        if p.id == student_id:
            return p
    raise KeyError(f"Student ID not found: '{student_id}'")


def random_recommend_teammates(
    student_id: str,
    k: int = 5,
    seed: int = 42,
) -> list[dict[str, Any]]:
    if k < 1:
        raise ValueError("Parameter 'k' must be at least 1.")
    profiles = load_profiles()
    target = _find_student(profiles, student_id)
    candidates = [p for p in profiles if p.id != target.id]

    rng = random.Random(seed)
    chosen = rng.sample(candidates, k=min(k, len(candidates)))
    results: list[dict[str, Any]] = []
    for cand in chosen:
        roles = infer_roles(cand.skills) or ["general"]
        results.append(
            {
                "student_id": cand.id,
                "score": round(rng.uniform(0.0, 1.0), 4),
                "roles_covered": roles,
                "reason": "random baseline selection",
            }
        )
    return results


def tfidf_recommend_teammates(student_id: str, k: int = 5) -> list[dict[str, Any]]:
    if k < 1:
        raise ValueError("Parameter 'k' must be at least 1.")
    profiles = load_profiles()
    target = _find_student(profiles, student_id)
    target_idx = next(i for i, p in enumerate(profiles) if p.id == target.id)

    docs = [
        " ".join(normalize_skills(p.skills) + p.interests + p.goals + [p.branch])
        for p in profiles
    ]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(docs)
    sims = cosine_similarity(tfidf_matrix[target_idx], tfidf_matrix).flatten()

    scored: list[tuple[float, dict[str, Any]]] = []
    for idx, cand in enumerate(profiles):
        if cand.id == target.id:
            continue
        sim = round(float(sims[idx]), 4)
        roles = infer_roles(cand.skills) or ["general"]
        scored.append(
            (
                sim,
                {
                    "student_id": cand.id,
                    "score": sim,
                    "roles_covered": roles,
                    "reason": "TF-IDF keyword similarity",
                },
            )
        )

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:k]]


def rule_based_recommend_teammates(student_id: str, k: int = 5) -> list[dict[str, Any]]:
    if k < 1:
        raise ValueError("Parameter 'k' must be at least 1.")
    profiles = load_profiles()
    target = _find_student(profiles, student_id)

    scored: list[tuple[float, dict[str, Any]]] = []
    for cand in profiles:
        if cand.id == target.id:
            continue
        same_branch = cand.branch.strip().lower() == target.branch.strip().lower()
        same_year = cand.year == target.year
        rule_score = (0.6 if same_branch else 0.0) + (0.4 if same_year else 0.0)
        roles = infer_roles(cand.skills) or ["general"]
        scored.append(
            (
                rule_score,
                {
                    "student_id": cand.id,
                    "score": round(rule_score, 4),
                    "roles_covered": roles,
                    "reason": f"rule baseline (branch={cand.branch}, year={cand.year})",
                },
            )
        )

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:k]]
