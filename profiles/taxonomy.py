from typing import Iterable


SKILL_TAXONOMY: dict[str, str] = {
    "ml": "machine learning",
    "machine learning": "machine learning",
    "dl": "deep learning",
    "deep learning": "deep learning",
    "nlp": "natural language processing",
    "natural language processing": "natural language processing",
    "cv": "computer vision",
    "computer vision": "computer vision",
    "py": "python",
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "ui": "ui/ux design",
    "ux": "ui/ux design",
    "ui/ux": "ui/ux design",
    "ui/ux design": "ui/ux design",
    "figma": "ui/ux design",
    "design": "ui/ux design",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "fastapi": "backend api",
    "flask": "backend api",
    "django": "backend api",
    "backend": "backend api",
    "sql": "sql",
    "postgres": "sql",
    "postgresql": "sql",
    "docker": "devops & cloud",
    "aws": "devops & cloud",
    "gcp": "devops & cloud",
    "cloud": "devops & cloud",
    "git": "git",
}


SKILL_TO_ROLE: dict[str, str] = {
    "machine learning": "ml",
    "deep learning": "ml",
    "natural language processing": "ml",
    "computer vision": "ml",
    "react": "frontend",
    "javascript": "frontend",
    "typescript": "frontend",
    "ui/ux design": "design",
    "node.js": "backend",
    "backend api": "backend",
    "sql": "backend",
    "python": "backend",
    "devops & cloud": "backend",
    "git": "backend",
}


def normalize_skill(skill: str) -> str:
    cleaned = " ".join(str(skill).strip().lower().split())
    if not cleaned:
        return ""
    return SKILL_TAXONOMY.get(cleaned, cleaned)


def normalize_skills(skills: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in skills:
        canon = normalize_skill(raw)
        if canon and canon not in seen:
            seen.add(canon)
            normalized.append(canon)
    return normalized


def infer_roles(skills: Iterable[str]) -> list[str]:
    roles: list[str] = []
    seen: set[str] = set()
    for canon in normalize_skills(skills):
        role = SKILL_TO_ROLE.get(canon)
        if role and role not in seen:
            seen.add(role)
            roles.append(role)
    return roles
