import csv
import html
import os
from pathlib import Path

import requests
import streamlit as st

API_URL = os.getenv("CAMPUSBUDDY_API_URL", "http://127.0.0.1:8000")
ITEMS_CSV = Path(__file__).resolve().parent.parent / "data" / "items" / "items.csv"
ROOT_DIR = Path(__file__).resolve().parent.parent

st.set_page_config(
    page_title="CampusBuddy — Campus Notice Board",
    page_icon="CB",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    :root {
        --bg: #F4F1EA;
        --surface: #FCFBF8;
        --ink: #18181B;
        --ink-muted: #57534E;
        --border: #D6D0C4;
        --offset: #E2DDD2;
        --green: #1F5E43;
        --green-soft: #E9F2ED;
        --green-border: #A9CBB9;
        --red: #C83E2B;
        --red-soft: #FCECE9;
        --red-border: #E7B2AA;
        --amber: #B45309;
        --amber-soft: #FEF4E6;
        --amber-border: #E8C794;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        background-color: #F4F1EA !important;
        color: #18181B !important;
    }

    header[data-testid="stHeader"] {
        background-color: #F4F1EA !important;
        border-bottom: 1px solid #D6D0C4;
    }

    section[data-testid="stSidebar"] {
        background-color: #EFECE3 !important;
        border-right: 1px solid #D6D0C4 !important;
    }

    .block-container {
        max-width: 1120px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4, p, span, label, div {
        color: #18181B;
    }

    .cb-muted { color: #57534E !important; font-size: 0.88rem; }
    .cb-mono { font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace !important; }

    /* Structured Paper Slips */
    .cb-slip {
        background-color: #FCFBF8;
        border: 1px solid #D6D0C4;
        border-radius: 6px;
        box-shadow: 2px 2px 0px #E2DDD2;
        padding: 1rem 1.15rem;
        margin-bottom: 0.85rem;
    }

    .cb-header-bar {
        background-color: #FCFBF8;
        border: 1px solid #D6D0C4;
        border-radius: 6px;
        box-shadow: 2px 2px 0px #E2DDD2;
        padding: 0.95rem 1.2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.85rem;
    }

    .cb-brand {
        display: flex;
        align-items: center;
        gap: 0.7rem;
    }

    .cb-mark {
        width: 32px;
        height: 32px;
        border-radius: 6px;
        background-color: #1F5E43;
        color: #FCFBF8 !important;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .cb-slip-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #18181B !important;
        margin-bottom: 0.2rem;
    }

    /* Crisp Tags */
    .cb-tag {
        display: inline-block;
        padding: 0.16rem 0.5rem;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        border: 1px solid #D6D0C4;
        background-color: #F4F1EA;
        color: #57534E !important;
        margin-right: 0.3rem;
        margin-bottom: 0.25rem;
    }

    .cb-tag-mono {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.71rem;
    }

    .cb-tag-green {
        background-color: #E9F2ED;
        border-color: #A9CBB9;
        color: #1F5E43 !important;
    }

    .cb-tag-red {
        background-color: #FCECE9;
        border-color: #E7B2AA;
        color: #C83E2B !important;
    }

    .cb-tag-amber {
        background-color: #FEF4E6;
        border-color: #E8C794;
        color: #B45309 !important;
    }

    .cb-why {
        background-color: #F4F1EA;
        border: 1px solid #D6D0C4;
        border-left: 3px solid #1F5E43;
        border-radius: 6px;
        padding: 0.55rem 0.75rem;
        font-size: 0.84rem;
        color: #18181B !important;
        margin-top: 0.55rem;
    }

    .cb-why-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 600;
        color: #57534E !important;
        text-transform: uppercase;
        display: block;
        margin-bottom: 0.12rem;
    }

    /* Inputs, Buttons, Tabs */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
        background-color: #FCFBF8 !important;
        color: #18181B !important;
        border: 1px solid #D6D0C4 !important;
        border-radius: 6px !important;
    }

    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        border: 1px solid #1F5E43 !important;
        background-color: #1F5E43 !important;
        color: #FCFBF8 !important;
        box-shadow: none !important;
    }

    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background-color: #174934 !important;
        border-color: #174934 !important;
        color: #FCFBF8 !important;
    }

    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #57534E !important;
        border-radius: 6px 6px 0 0 !important;
        font-weight: 600 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FCFBF8 !important;
        color: #1F5E43 !important;
        border: 1px solid #D6D0C4 !important;
        border-bottom-color: #FCFBF8 !important;
    }

    div[data-testid="stExpander"] {
        background-color: #FCFBF8 !important;
        border: 1px solid #D6D0C4 !important;
        border-radius: 6px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {
        "student_id": "S001",
        "connected_ids": set(),
        "checked_in_events": set(),
        "going_open": set(),
        "lost_notices": [],
        "session_found_items": [],
        "desk_history": [],
        "lf_search_hits": None,
        "selected_item_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def api_get(path: str, params: dict | None = None):
    try:
        res = requests.get(f"{API_URL}{path}", params=params, timeout=5)
        return res
    except Exception:
        return None


def api_post(path: str, json_body: dict | None = None, data: dict | None = None, files: dict | None = None):
    try:
        res = requests.post(f"{API_URL}{path}", json=json_body, data=data, files=files, timeout=10)
        return res
    except Exception:
        return None


@st.cache_data(ttl=15)
def load_all_profiles_cached() -> list[dict]:
    res = api_get("/profiles")
    if res is not None and res.status_code == 200:
        return res.json()
    return []


def load_local_items_catalog() -> list[dict]:
    items: list[dict] = []
    if ITEMS_CSV.exists():
        with ITEMS_CSV.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                items.append(
                    {
                        "item_id": row.get("item_id", ""),
                        "description": row.get("description", ""),
                        "category": row.get("category", ""),
                        "color": row.get("color", ""),
                        "location": row.get("location", ""),
                        "date": row.get("date", ""),
                        "image_path": row.get("image_path", ""),
                        "status": "FOUND",
                    }
                )
    return items


init_state()

profiles_list = load_all_profiles_cached()
profiles_by_id = {p["id"]: p for p in profiles_list}
backend_online = len(profiles_list) > 0
if not backend_online:
    health_res = api_get("/health")
    backend_online = health_res is not None and health_res.status_code == 200

notifs_res = api_get("/notifications")
notifs = notifs_res.json() if notifs_res is not None and notifs_res.status_code == 200 else []

# ---------- TOP HEADER & STUDENT CONTEXT BAR ----------
status_badge = (
    '<span class="cb-tag cb-tag-mono cb-tag-green">● API ONLINE</span>'
    if backend_online
    else '<span class="cb-tag cb-tag-mono cb-tag-red">● API OFFLINE</span>'
)

st.markdown(
    f"""
    <div class="cb-header-bar">
        <div class="cb-brand">
            <span class="cb-mark">CB</span>
            <div>
                <div style="font-size:1.12rem; font-weight:700; line-height:1.15;">CampusBuddy</div>
                <div class="cb-mono" style="font-size:0.7rem; color:#57534E; text-transform:uppercase; letter-spacing:0.04em;">Department Notice Board</div>
            </div>
        </div>
        <div>
            {status_badge}
            <span class="cb-tag cb-tag-mono">ALERTS: {len(notifs)}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

ctx_col1, ctx_col2 = st.columns([2.2, 3.8])
with ctx_col1:
    if profiles_list:
        sorted_profiles = sorted(profiles_list, key=lambda p: p["id"])
        options = [p["id"] for p in sorted_profiles]
        curr_idx = options.index(st.session_state.student_id) if st.session_state.student_id in options else 0
        chosen_id = st.selectbox(
            "Active student profile",
            options,
            index=curr_idx,
            format_func=lambda pid: f"{pid} — {profiles_by_id[pid]['name']} ({profiles_by_id[pid]['branch']} · Yr {profiles_by_id[pid]['year']})",
        )
        st.session_state.student_id = chosen_id
    else:
        entered = st.text_input("Active student ID", value=st.session_state.student_id).strip()
        if entered:
            st.session_state.student_id = entered

sid = st.session_state.student_id
active_profile = profiles_by_id.get(sid)
if active_profile is None and backend_online:
    p_res = api_get(f"/profiles/{sid}")
    if p_res is not None and p_res.status_code == 200:
        active_profile = p_res.json()
        profiles_by_id[sid] = active_profile

active_profile = active_profile or {}
vis = active_profile.get("visibility", {"share_events": True, "ghost_mode": False})

if vis.get("ghost_mode"):
    priv_html = '<span class="cb-tag cb-tag-amber">Ghost Mode Active</span>'
elif vis.get("share_events", True):
    priv_html = '<span class="cb-tag cb-tag-green">Event Sharing On</span>'
else:
    priv_html = '<span class="cb-tag">Events Private</span>'

with ctx_col2:
    avail_str = " · ".join(d.upper() for d in active_profile.get("availability", [])) or "FLEXIBLE"
    skills_str = ", ".join(active_profile.get("skills", [])[:5]) or "None listed"
    st.markdown(
        f"""
        <div class="cb-slip" style="margin-bottom:0.4rem; padding:0.7rem 0.95rem;">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.4rem;">
                <div>
                    <strong>{html.escape(active_profile.get('name', sid))}</strong>
                    <span class="cb-tag cb-tag-mono">{html.escape(sid)}</span>
                    <span class="cb-tag">{html.escape(active_profile.get('branch', 'Campus'))} · Year {html.escape(str(active_profile.get('year', '-')))}</span>
                    <span class="cb-tag cb-tag-mono">{html.escape(avail_str)}</span>
                    {priv_html}
                </div>
            </div>
            <div class="cb-muted" style="margin-top:0.25rem; font-size:0.8rem;">Skills: {html.escape(skills_str)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander("Edit profile & privacy settings"):
    with st.form("profile_editor_form"):
        c1, c2, c3 = st.columns([1.2, 1.8, 1.5])
        f_id = c1.text_input("Student ID", value=active_profile.get("id", sid))
        f_name = c2.text_input("Display Name", value=active_profile.get("name", f"Student_{sid}"))
        f_email = c3.text_input("College Email (optional)", placeholder="name@college.edu.in")

        c4, c5, c6 = st.columns(3)
        branches = ["CSE", "ISE", "ECE", "EEE", "AIML", "MECH"]
        curr_b = active_profile.get("branch", "CSE")
        f_year = c4.number_input("Academic Year", min_value=1, max_value=6, value=int(active_profile.get("year", 1)))
        f_branch = c5.selectbox("Department", branches, index=branches.index(curr_b) if curr_b in branches else 0)
        roles = ["mentee", "mentor", "both"]
        curr_r = active_profile.get("role", "mentee")
        f_role = c6.selectbox("Role", roles, index=roles.index(curr_r) if curr_r in roles else 0)

        f_skills = st.text_input("Skills (comma-separated)", value=", ".join(active_profile.get("skills", [])))
        c7, c8 = st.columns(2)
        f_interests = c7.text_input("Interests", value=", ".join(active_profile.get("interests", [])))
        f_goals = c8.text_input("Goals", value=", ".join(active_profile.get("goals", [])))
        f_avail = st.multiselect(
            "Weekly availability",
            ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            default=[d for d in active_profile.get("availability", ["sat", "sun"]) if d in {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}],
        )
        p1, p2 = st.columns(2)
        f_share = p1.toggle("Share event check-ins with peers", value=bool(vis.get("share_events", True)))
        f_ghost = p2.toggle("Ghost mode (hide from attendee lists)", value=bool(vis.get("ghost_mode", False)))

        if st.form_submit_button("Save profile & privacy"):
            payload = {
                "id": f_id.strip(),
                "name": f_name.strip(),
                "email": f_email.strip() or None,
                "year": int(f_year),
                "branch": f_branch,
                "role": f_role,
                "skills": [s.strip() for s in f_skills.split(",") if s.strip()],
                "interests": [s.strip() for s in f_interests.split(",") if s.strip()],
                "goals": [s.strip() for s in f_goals.split(",") if s.strip()],
                "availability": f_avail,
                "visibility": {"share_events": f_share, "ghost_mode": f_ghost},
            }
            save_res = api_post("/profiles", json_body=payload)
            if save_res is not None and save_res.status_code == 200:
                st.session_state.student_id = f_id.strip()
                load_all_profiles_cached.clear()
                st.success("Profile and privacy settings saved.")
                st.rerun()
            else:
                detail = save_res.json().get("detail") if save_res is not None else "Backend unavailable."
                st.error(detail)

# ---------- 4 CORE MODULE TABS ----------
tab_match, tab_events, tab_lf, tab_desk = st.tabs(
    [
        "Find teammates",
        "Events & going together",
        "Lost & found",
        "Campus rules & timetables",
    ]
)

# ==========================================
# 1. TEAMMATE & MENTOR MATCHING
# ==========================================
with tab_match:
    st.markdown("### Find teammates & mentors")
    st.markdown('<p class="cb-muted">Profile slips matched on complementary technical skills, weekly availability, and branch alignment.</p>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.3, 2.2, 0.9])
    role_filter = f1.selectbox("Role", ["All", "Teammates", "Mentors"], key="m_role_filter")
    skill_query = f2.text_input("Filter by skill, branch, or keyword", placeholder="e.g. python, machine learning, react, CSE", key="m_skill_query").strip().lower()
    top_k = f3.selectbox("Top K", [5, 8, 12], index=1, key="m_top_k")

    tm_res = api_get("/match/teammates", params={"student_id": sid, "k": top_k})
    mn_res = api_get("/match/mentors", params={"student_id": sid, "k": top_k})

    tm_list = [dict(m, match_type="TEAMMATE") for m in (tm_res.json() if tm_res is not None and tm_res.status_code == 200 else [])]
    mn_list = [dict(m, match_type="MENTOR") for m in (mn_res.json() if mn_res is not None and mn_res.status_code == 200 else [])]

    combined = []
    if role_filter in ("All", "Teammates"):
        combined.extend(tm_list)
    if role_filter in ("All", "Mentors"):
        combined.extend(mn_list)

    my_skills = {s.lower() for s in active_profile.get("skills", [])}
    filtered_matches = []
    for m in combined:
        prof = profiles_by_id.get(m["student_id"], {})
        haystack = " ".join(
            [
                m["student_id"],
                prof.get("name", ""),
                prof.get("branch", ""),
                m.get("reason", ""),
                *prof.get("skills", []),
                *prof.get("interests", []),
                *m.get("roles_covered", []),
            ]
        ).lower()
        if skill_query and skill_query not in haystack:
            continue
        filtered_matches.append(m)

    if not backend_online:
        st.info("Start the backend server (`python run.py`) to load teammate and mentor matches.")
    elif not filtered_matches:
        st.info("No matching profiles for this filter. Clear the keyword filter or switch to All roles.")
    else:
        cols = st.columns(2)
        for idx, m in enumerate(filtered_matches):
            prof = profiles_by_id.get(m["student_id"], {})
            cand_id = m["student_id"]
            cand_name = prof.get("name", cand_id)
            cand_branch = prof.get("branch", "Campus")
            cand_year = prof.get("year")
            pct = min(100, max(1, int(round(m.get("score", 0) * 100))))
            is_mentor = m["match_type"] == "MENTOR"
            role_tag = '<span class="cb-tag cb-tag-amber">MENTOR</span>' if is_mentor else '<span class="cb-tag cb-tag-green">TEAMMATE</span>'
            avail_text = " · ".join(d.upper() for d in prof.get("availability", [])) or "Flexible"

            skill_pills = "".join(
                f'<span class="cb-tag cb-tag-green">✓ {html.escape(s)}</span>'
                if s.lower() in my_skills
                else f'<span class="cb-tag">{html.escape(s)}</span>'
                for s in prof.get("skills", [])
            )
            roles_line = (
                f'<div style="margin-top:0.25rem;"><span class="cb-tag cb-tag-mono">ROLES: {html.escape(", ".join(m["roles_covered"]).upper())}</span></div>'
                if m.get("roles_covered")
                else ""
            )

            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="cb-slip">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem;">
                            <div>
                                <div class="cb-slip-title">{html.escape(cand_name)} <span class="cb-tag cb-tag-mono">{html.escape(cand_id)}</span> {role_tag}</div>
                                <div class="cb-muted">{html.escape(cand_branch)}{f' · Year {cand_year}' if cand_year else ''} · <span class="cb-mono">FREE: {html.escape(avail_text)}</span></div>
                            </div>
                            <span class="cb-tag cb-tag-mono cb-tag-green">{pct}% MATCH</span>
                        </div>
                        {roles_line}
                        <div style="margin-top:0.5rem;">{skill_pills or '<span class="cb-tag">No skills listed</span>'}</div>
                        <div class="cb-why">
                            <span class="cb-why-label">Why you match</span>
                            {html.escape(m.get("reason", ""))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                conn_key = f"{sid}:{m['match_type']}:{cand_id}"
                is_req = conn_key in st.session_state.connected_ids
                act_c1, act_c2 = st.columns([1.2, 1.8])
                if act_c1.button("Request sent ✓" if is_req else "Request connect", key=f"conn_{m['match_type']}_{cand_id}_{idx}"):
                    if is_req:
                        st.session_state.connected_ids.discard(conn_key)
                    else:
                        st.session_state.connected_ids.add(conn_key)
                    st.rerun()
                if is_mentor:
                    with act_c2:
                        r_c1, r_c2 = st.columns([1.2, 1])
                        rating = r_c1.selectbox("Rating", [5, 4, 3, 2, 1], key=f"rate_sel_{cand_id}_{idx}", label_visibility="collapsed")
                        if r_c2.button("Rate", key=f"rate_btn_{cand_id}_{idx}"):
                            fb = api_post("/mentors/feedback", json_body={"mentee_id": sid, "mentor_id": cand_id, "rating": rating})
                            if fb is not None and fb.status_code == 200:
                                st.success(f"Avg: {fb.json()['avg_rating']}/5")

# ==========================================
# 2. EVENTS & GOING TOGETHER
# ==========================================
with tab_events:
    st.markdown("### Events & going together")
    st.markdown('<p class="cb-muted">Chronological campus schedule with peer check-ins and privacy-safe attendance lists.</p>', unsafe_allow_html=True)

    ev_filter = st.radio("Filter events", ["All events", "Recommended", "Checked in"], horizontal=True, label_visibility="collapsed")

    ev_res = api_get("/events")
    rec_res = api_get("/events/recommend", params={"student_id": sid, "k": 4})

    events_data = sorted(ev_res.json(), key=lambda e: e.get("date", "")) if ev_res is not None and ev_res.status_code == 200 else []
    rec_map = {r["event_id"]: r for r in (rec_res.json() if rec_res is not None and rec_res.status_code == 200 else [])}

    visible_events = [
        ev for ev in events_data
        if (ev_filter == "All events")
        or (ev_filter == "Recommended" and ev["event_id"] in rec_map)
        or (ev_filter == "Checked in" and ev["event_id"] in st.session_state.checked_in_events)
    ]

    if not backend_online:
        st.info("Start the backend server (`python run.py`) to view campus events.")
    elif not visible_events:
        st.info("No events match the selected filter.")
    else:
        ev_cols = st.columns(2)
        for idx, ev in enumerate(visible_events):
            eid = ev["event_id"]
            rec = rec_map.get(eid)
            tags_html = "".join(f'<span class="cb-tag">{html.escape(t)}</span>' for t in ev.get("tags", []))
            rec_badge = '<span class="cb-tag cb-tag-green">RECOMMENDED</span>' if rec else ""
            rec_box = (
                f'<div class="cb-why"><span class="cb-why-label">Recommended for you</span>{html.escape(rec["reason"])}</div>'
                if rec
                else ""
            )

            with ev_cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="cb-slip">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem;">
                            <div>
                                <span class="cb-tag cb-tag-amber">EVENT</span>
                                <span class="cb-tag cb-tag-mono">{html.escape(ev.get('type', 'campus').upper())}</span>
                                {rec_badge}
                            </div>
                            <span class="cb-tag cb-tag-mono">{html.escape(ev['date'])}</span>
                        </div>
                        <div class="cb-slip-title" style="margin-top:0.35rem;">{html.escape(ev['title'])}</div>
                        <div class="cb-muted"><span class="cb-tag cb-tag-mono">{html.escape(eid)}</span> Venue: <strong>{html.escape(ev['venue'])}</strong></div>
                        <div style="margin-top:0.4rem;">{tags_html}</div>
                        {rec_box}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                b1, b2 = st.columns(2)
                is_going = eid in st.session_state.checked_in_events
                if b1.button("Going ✓" if is_going else "Check in (I'm going)", key=f"ev_chk_{eid}"):
                    chk = api_post(f"/events/{eid}/checkin", json_body={"student_id": sid})
                    if chk is not None and chk.status_code == 200:
                        st.session_state.checked_in_events.add(eid)
                        st.rerun()
                    else:
                        st.error("Check-in failed.")

                peers_open = eid in st.session_state.going_open
                if b2.button("Hide peers" if peers_open else "Going together / peers", key=f"ev_gt_{eid}"):
                    if peers_open:
                        st.session_state.going_open.discard(eid)
                    else:
                        st.session_state.going_open.add(eid)
                    st.rerun()

                if eid in st.session_state.going_open:
                    gt_res = api_get(f"/events/{eid}/going-together", params={"student_id": sid, "k": 3})
                    att_res = api_get(f"/events/{eid}/attendees", params={"viewer_id": sid})
                    if att_res is not None and att_res.status_code == 200:
                        gt_data = gt_res.json() if gt_res is not None and gt_res.status_code == 200 else {}
                        att_list = att_res.json()
                        st.info(gt_data.get("message", ""))
                        if att_list:
                            chips = "".join(
                                f'<span class="cb-tag cb-tag-green">{html.escape(a["name"])} ({html.escape(a["student_id"])})</span>'
                                for a in att_list
                            )
                            st.markdown(chips, unsafe_allow_html=True)
                        else:
                            st.caption("No public attendees visible (ghost-mode and opted-out students remain hidden).")
                    else:
                        st.caption("Save your profile first to view peers attending.")

# ==========================================
# 3. LOST & FOUND
# ==========================================
with tab_lf:
    st.markdown("### Lost & found")
    st.markdown('<p class="cb-muted">Photo-indexed items turned in across campus, plus lost notices and ownership verification.</p>', unsafe_allow_html=True)

    lf_filter_col, lf_q_col, lf_loc_col = st.columns([1.4, 2, 1.2])
    lf_status = lf_filter_col.radio("Status", ["All", "Found", "Lost"], horizontal=True, label_visibility="collapsed")
    lf_q = lf_q_col.text_input("Search lost/found inventory", placeholder="e.g. blue steel bottle, black calculator", label_visibility="collapsed")
    lf_loc = lf_loc_col.text_input("Last seen location", placeholder="Location (optional)", label_visibility="collapsed")
    lf_photo = st.file_uploader("Optional reference photo for similarity search", type=["jpg", "jpeg", "png", "webp"], key="lf_search_photo")

    s_c1, s_c2 = st.columns([1, 4])
    if s_c1.button("Search match"):
        if not lf_q.strip() and not lf_photo:
            st.warning("Enter a description or attach a photo to search.")
        else:
            files = {"image": (lf_photo.name, lf_photo.getvalue(), lf_photo.type)} if lf_photo else None
            data = {"description": lf_q.strip(), "location": lf_loc.strip(), "k": "6", "student_id": sid}
            sr = api_post("/items/lost", data=data, files=files)
            if sr is not None and sr.status_code == 200:
                st.session_state.lf_search_hits = sr.json()
            else:
                st.error("Search failed.")
    if st.session_state.lf_search_hits is not None and s_c2.button("Show full inventory"):
        st.session_state.lf_search_hits = None
        st.rerun()

    with st.expander("+ Post lost notice or report found item"):
        sub_lost, sub_found = st.tabs(["Post lost notice", "Report found item"])
        with sub_lost:
            with st.form("post_lost_form"):
                l_desc = st.text_input("Item description*", placeholder="Black Casio scientific calculator")
                lc1, lc2, lc3 = st.columns(3)
                l_loc = lc1.text_input("Last seen location*", placeholder="LH-204")
                l_date = lc2.text_input("Date lost*", value="2026-11-24")
                l_cat = lc3.text_input("Category", placeholder="calculator, bottle, id_card")
                if st.form_submit_button("Post lost notice"):
                    if l_desc.strip() and l_loc.strip():
                        nid = f"LOST_{len(st.session_state.lost_notices) + 1:03d}"
                        st.session_state.lost_notices.insert(
                            0,
                            {
                                "item_id": nid,
                                "description": l_desc.strip(),
                                "category": l_cat.strip() or "item",
                                "color": "",
                                "location": l_loc.strip(),
                                "date": l_date.strip(),
                                "image_path": "",
                                "status": "LOST",
                            },
                        )
                        st.success(f"Posted {nid} on notice board.")
                        st.rerun()
                    else:
                        st.warning("Provide description and location.")

        with sub_found:
            with st.form("report_found_form"):
                f_desc = st.text_input("Item description*", placeholder="Silver stainless steel flask")
                fc1, fc2 = st.columns(2)
                f_loc = fc1.text_input("Found location*", placeholder="Main Auditorium")
                f_date = fc2.text_input("Date found*", value="2026-11-24")
                fc3, fc4, fc5 = st.columns(3)
                f_cat = fc3.text_input("Category", placeholder="bottle")
                f_col = fc4.text_input("Color", placeholder="silver")
                f_sec = fc5.text_input("Hidden verification detail", placeholder="sticker on bottom")
                f_img = st.file_uploader("Upload photo*", type=["jpg", "jpeg", "png", "webp"], key="found_upload")
                if st.form_submit_button("Add found item"):
                    if not f_desc.strip() or not f_loc.strip() or not f_img:
                        st.warning("Provide description, location, and photo.")
                    else:
                        files = {"image": (f_img.name, f_img.getvalue(), f_img.type)}
                        data = {
                            "description": f_desc.strip(),
                            "location": f_loc.strip(),
                            "date": f_date.strip(),
                            "category": f_cat.strip(),
                            "color": f_col.strip(),
                            "secret_detail": f_sec.strip(),
                        }
                        fr = api_post("/items/found", data=data, files=files)
                        if fr is not None and fr.status_code == 200:
                            new_id = fr.json()["item_id"]
                            st.session_state.session_found_items.insert(
                                0,
                                {
                                    "item_id": new_id,
                                    "description": f_desc.strip(),
                                    "category": f_cat.strip() or "item",
                                    "color": f_col.strip(),
                                    "location": f_loc.strip(),
                                    "date": f_date.strip(),
                                    "image_bytes": f_img.getvalue(),
                                    "status": "FOUND",
                                },
                            )
                            st.success(f"Found item indexed as {new_id}.")
                            st.rerun()
                        else:
                            st.error("Failed to upload found item.")

    catalog = st.session_state.lost_notices + st.session_state.session_found_items + load_local_items_catalog()
    catalog_map = {item["item_id"]: item for item in catalog}

    if st.session_state.lf_search_hits is not None:
        display_items = []
        for h in st.session_state.lf_search_hits:
            base = catalog_map.get(h["item_id"], {})
            display_items.append(
                {
                    "item_id": h["item_id"],
                    "description": base.get("description", f"Found item {h['item_id']}"),
                    "category": base.get("category", "item"),
                    "color": base.get("color", ""),
                    "location": h.get("location") or base.get("location", ""),
                    "date": h.get("date") or base.get("date", ""),
                    "image_path": base.get("image_path", ""),
                    "image_bytes": base.get("image_bytes"),
                    "status": "FOUND",
                    "score": h.get("score"),
                    "notify": h.get("notify", False),
                }
            )
    else:
        display_items = [
            it for it in catalog
            if lf_status == "All" or it["status"] == lf_status.upper()
        ]

    if not display_items:
        st.info("No items match this view.")
    else:
        lf_cols = st.columns(3)
        for idx, item in enumerate(display_items):
            with lf_cols[idx % 3]:
                if item.get("image_bytes"):
                    st.image(item["image_bytes"], use_container_width=True)
                elif item.get("image_path") and (ROOT_DIR / item["image_path"]).exists():
                    st.image(str(ROOT_DIR / item["image_path"]), use_container_width=True)

                is_lost = item["status"] == "LOST"
                st_tag = '<span class="cb-tag cb-tag-mono cb-tag-red">LOST</span>' if is_lost else '<span class="cb-tag cb-tag-mono cb-tag-green">FOUND</span>'
                score_tag = (
                    f'<span class="cb-tag cb-tag-mono cb-tag-green">{int(round(item["score"] * 100))}% MATCH</span>'
                    if isinstance(item.get("score"), (int, float))
                    else ""
                )
                st.markdown(
                    f"""
                    <div class="cb-slip">
                        <div>
                            {st_tag}
                            <span class="cb-tag cb-tag-mono">{html.escape(item['item_id'])}</span>
                            {score_tag}
                        </div>
                        <div class="cb-slip-title" style="font-size:0.95rem; margin-top:0.3rem;">{html.escape(item['description'])}</div>
                        <div class="cb-muted cb-mono" style="font-size:0.78rem;">{html.escape(item['location'])} · {html.escape(item['date'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if not is_lost and st.button("Claim / details", key=f"claim_btn_{item['item_id']}_{idx}"):
                    st.session_state.selected_item_id = item["item_id"]

    if st.session_state.selected_item_id:
        sel_item = catalog_map.get(st.session_state.selected_item_id)
        if sel_item:
            st.markdown("---")
            st.markdown(f"#### Claim verification — {sel_item['item_id']}: {sel_item['description']}")
            v_ans = st.text_input("Describe a hidden mark or unique detail", placeholder="e.g. dented bottom left, initials SK on back", key="verify_ans_input")
            vc1, vc2 = st.columns([1, 4])
            if vc1.button("Verify claim"):
                vr = api_post("/items/verify", json_body={"item_id": sel_item["item_id"], "claimer_answer": v_ans})
                if vr is not None and vr.status_code == 200:
                    out = vr.json()
                    pct = int(round(out.get("similarity", 0) * 100))
                    if out.get("verified"):
                        st.success(f"Ownership verified ({pct}% match) — ready for handover.")
                    else:
                        st.warning(f"Detail did not match finder's record ({pct}% match).")
                else:
                    st.error("Verification service unavailable.")
            if vc2.button("Close details"):
                st.session_state.selected_item_id = None
                st.rerun()

# ==========================================
# 4. CAMPUS RULES & TIMETABLES (CIRCULAR DESK)
# ==========================================
with tab_desk:
    st.markdown("### Campus rules & timetables")
    st.markdown('<p class="cb-muted">Official circular desk — answers are grounded in verified campus markdown documents with citations.</p>', unsafe_allow_html=True)

    sample_questions = [
        ("Attendance policy", "What is the minimum attendance requirement?"),
        ("Exam rules", "What are the hall ticket and exam hall rules?"),
        ("Canteen & library timings", "What are the library timings?"),
        ("CSE 5th sem timetable", "On which day is the DBMS lab for CSE 5th semester section A?"),
    ]

    sq_cols = st.columns(4)
    chosen_q = None
    for i, (label, q_text) in enumerate(sample_questions):
        if sq_cols[i].button(label, key=f"sq_{i}", use_container_width=True):
            chosen_q = q_text

    with st.form("desk_form", clear_on_submit=True):
        dq_c1, dq_c2 = st.columns([4.5, 1])
        typed_q = dq_c1.text_input("Ask a question", placeholder="Ask about attendance, exam rules, library, hostel, fees, or timetable...", label_visibility="collapsed")
        submitted = dq_c2.form_submit_button("Ask desk", use_container_width=True)
        if submitted and typed_q.strip():
            chosen_q = typed_q.strip()

    if chosen_q:
        ans_res = api_post("/assistant/ask", json_body={"question": chosen_q})
        if ans_res is not None and ans_res.status_code == 200:
            payload = ans_res.json()
            st.session_state.desk_history.insert(
                0,
                {
                    "question": chosen_q,
                    "answer": payload.get("answer", ""),
                    "sources": payload.get("sources", []),
                },
            )
        else:
            st.session_state.desk_history.insert(
                0,
                {
                    "question": chosen_q,
                    "answer": "Assistant service unavailable.",
                    "sources": [],
                },
            )

    if not st.session_state.desk_history:
        st.info("Select a quick circular question above or type your own question to view the grounded answer and citations.")
    else:
        for entry in st.session_state.desk_history:
            srcs = entry.get("sources", [])
            if srcs:
                src_badges = "".join(
                    f'<span class="cb-tag cb-tag-mono cb-tag-green">📄 {html.escape(s["source"])} · {html.escape(s["section"])}'
                    + (f' · {s["score"]:.2f}' if isinstance(s.get("score"), (int, float)) else "")
                    + "</span>"
                    for s in srcs
                )
            else:
                src_badges = '<span class="cb-tag cb-tag-mono">NO MATCHING CIRCULAR FOUND</span>'

            st.markdown(
                f"""
                <div class="cb-slip">
                    <div style="border-bottom:1px solid #D6D0C4; padding-bottom:0.45rem; margin-bottom:0.5rem;">
                        <span class="cb-tag cb-tag-mono">QUERY</span>
                        <strong>{html.escape(entry["question"])}</strong>
                    </div>
                    <div style="font-size:0.94rem; line-height:1.55;">{html.escape(entry["answer"])}</div>
                    <div style="margin-top:0.65rem; padding-top:0.55rem; border-top:1px dashed #D6D0C4;">
                        <span class="cb-tag cb-tag-mono">CITED DOCS</span>
                        {src_badges}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
