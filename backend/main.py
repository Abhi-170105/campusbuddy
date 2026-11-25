import os; os.environ.setdefault("CAMPUSBUDDY_LLM", "none")
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from backend import adapter, profile_store

# Paths are built from this file's location, so the server works from any folder
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB limit

app = FastAPI(
    title="CampusBuddy API",
    description="Unified REST API for CampusBuddy (Teammates, Mentors, Lost & Found, Events, Campus Assistant)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NOTIFICATIONS: list[dict[str, Any]] = []
profile_store.sync_all_to_event_store()


class VisibilityModel(BaseModel):
    share_events: bool = True
    ghost_mode: bool = False


class ProfileIn(BaseModel):
    id: str
    name: str
    year: int = Field(..., ge=1, le=6)
    branch: str
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    availability: list[str] = Field(default_factory=list)
    role: str = "mentee"
    email: str | None = None
    visibility: VisibilityModel = Field(default_factory=VisibilityModel)


class FeedbackIn(BaseModel):
    mentee_id: str
    mentor_id: str
    rating: float = Field(..., ge=1, le=5)


class CheckinIn(BaseModel):
    student_id: str


class AskIn(BaseModel):
    question: str


class VerifyClaimIn(BaseModel):
    item_id: str
    claimer_answer: str


def _save_upload(upload: UploadFile) -> str:
    ext = Path(upload.filename or "upload.jpg").suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image format. Use JPG, PNG, or WEBP.")
    content = upload.file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 5MB limit.")
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    dest.write_bytes(content)
    return str(dest)



@app.get("/")
def serve_frontend() -> FileResponse:
    # no-cache: the browser checks for a newer page each time (the service worker keeps an offline copy)
    return FileResponse(FRONTEND_DIR / "index.html", headers={"Cache-Control": "no-cache"})


# ---------- PWA files (installable phone app) ----------
# They must be served from the site root: the service worker can only control
# pages at or below the path it is served from.

@app.get("/manifest.webmanifest", include_in_schema=False)
def pwa_manifest() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def pwa_service_worker() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
    )


@app.get("/offline.html", include_in_schema=False)
def pwa_offline_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "offline.html")


PWA_ICONS = {"icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"}


@app.get("/icons/{name}", include_in_schema=False)
def pwa_icon(name: str) -> FileResponse:
    if name not in PWA_ICONS:                      # only known files, no path tricks
        raise HTTPException(status_code=404, detail="Icon not found.")
    return FileResponse(FRONTEND_DIR / "icons" / name, media_type="image/png")

@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/notifications")
def list_notifications() -> list[dict[str, Any]]:
    return list(reversed(NOTIFICATIONS))


@app.get("/admin/stats")
def admin_stats() -> dict[str, Any]:
    profiles = profile_store.get_all_profiles()
    from events.checkins import get_store
    store = get_store()
    return {
        "total_students": len(profiles),
        "ghost_mode_students": sum(1 for p in profiles if p["visibility"]["ghost_mode"]),
        "total_events": len(store.events),
        "total_checkins": len(store.going),
        "notifications_sent": len(NOTIFICATIONS),
    }


@app.post("/profiles")
def create_or_update_profile(payload: ProfileIn) -> dict[str, Any]:
    try:
        return profile_store.upsert_profile(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/profiles")
def list_profiles() -> list[dict[str, Any]]:
    return profile_store.get_all_profiles()


@app.get("/profiles/{student_id}")
def read_profile(student_id: str) -> dict[str, Any]:
    prof = profile_store.get_profile(student_id)
    if prof is None:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
    return prof


@app.get("/match/teammates")
def get_teammates(
    student_id: str = Query(...),
    event_id: str | None = Query(default=None),
    k: int = Query(default=5, ge=1, le=20),
) -> list[dict[str, Any]]:
    try:
        return adapter.call_recommend_teammates(student_id=student_id, event_id=event_id, k=k)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/match/mentors")
def get_mentors(
    student_id: str = Query(...),
    k: int = Query(default=5, ge=1, le=20),
) -> list[dict[str, Any]]:
    try:
        return adapter.call_recommend_mentors(student_id=student_id, k=k)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/mentors/feedback")
def post_mentor_feedback(payload: FeedbackIn) -> dict[str, Any]:
    try:
        return adapter.call_record_mentor_feedback(
            mentee_id=payload.mentee_id,
            mentor_id=payload.mentor_id,
            rating=payload.rating,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/items/found")
def report_found_item(
    description: str = Form(...),
    location: str = Form(...),
    date: str = Form(...),
    category: str = Form(default=""),
    color: str = Form(default=""),
    secret_detail: str = Form(default=""),
    image: UploadFile = File(...),
) -> dict[str, Any]:
    saved_path = _save_upload(image)
    try:
        item_id = adapter.call_add_found_item(
            image_path=saved_path,
            description=description,
            location=location,
            date=date,
            category=category,
            color=color,
            secret_detail=secret_detail,
        )
        return {"item_id": item_id, "status": "added"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/items/lost")
def search_lost(
    description: str = Form(default=""),
    k: int = Form(default=5),
    category: str | None = Form(default=None),
    location: str | None = Form(default=None),
    date: str | None = Form(default=None),
    student_id: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
) -> list[dict[str, Any]]:
    saved_path = _save_upload(image) if image and image.filename else None
    try:
        hits = adapter.call_search_lost_item(
            description=description,
            image_path=saved_path,
            k=k,
            category=category or None,
            location=location or None,
            date=date or None,
        )
        for h in hits:
            if h.get("notify"):
                NOTIFICATIONS.append({
                    "student_id": student_id or "anonymous",
                    "item_id": h["item_id"],
                    "score": h["score"],
                    "message": f"Likely match found ({h['item_id']}) at {h['location']} on {h['date']}!",
                })
        return hits
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/items/verify")
def verify_item_claim(payload: VerifyClaimIn) -> dict[str, Any]:
    try:
        return adapter.call_verify_ownership(payload.item_id, payload.claimer_answer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/events")
def list_events() -> list[dict[str, Any]]:
    from events.data import load_events
    return load_events()


@app.post("/events/{event_id}/checkin")
def event_checkin(event_id: str, payload: CheckinIn) -> dict[str, Any]:
    try:
        return adapter.call_checkin(student_id=payload.student_id, event_id=event_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/events/{event_id}/attendees")
def event_attendees(
    event_id: str,
    viewer_id: str = Query(..., description="Logged-in student ID; anonymous access forbidden"),
) -> list[dict[str, Any]]:
    try:
        return adapter.call_attendees(event_id=event_id, viewer_id=viewer_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/events/{event_id}/going-together")
def event_going_together(
    event_id: str,
    student_id: str = Query(...),
    k: int = Query(default=3, ge=1, le=10),
) -> dict[str, Any]:
    try:
        return adapter.call_going_together(student_id=student_id, event_id=event_id, k=k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/events/recommend")
def event_recommendations(
    student_id: str = Query(...),
    k: int = Query(default=5, ge=1, le=20),
) -> list[dict[str, Any]]:
    try:
        return adapter.call_recommend_events(student_id=student_id, k=k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/assistant/ask")
def ask_campus_assistant(payload: AskIn) -> dict[str, Any]:
    return adapter.call_ask_assistant(question=payload.question)
