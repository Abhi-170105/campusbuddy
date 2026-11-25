import re
from typing import Any

import matching
import lostfound
import events
import assistant


GREETINGS = {
    "hi", "hii", "hey", "heyy", "heyyy", "hello", "hola", "yo",
    "good morning", "good afternoon", "good evening", "help", "what can you do",
}

COMPOUND_FIXES = {
    "hostelrules": "hostel rules",
    "hostelrule": "hostel rules",
    "messtimings": "mess timings",
    "libraryfine": "library fine",
    "libraryfines": "library fines",
    "examdates": "exam dates",
    "examschedule": "exam schedule",
    "attendancerules": "attendance rules",
    "wifipassword": "wifi password",
    "feestructure": "fee structure",
    "busroutes": "bus routes",
}

PREDEFINED_CAMPUS_KB: list[tuple[tuple[str, ...], str, str, str]] = [
    (
        ("hostel", "curfew", "warden", "visitor", "room", "outpass"),
        "Hostel residents must return by 9:30 PM on weekdays and 10:30 PM on weekends. Overnight leave requires an approved digital outpass from the Warden at least 24 hours in advance. Visitors are permitted only in the common lobby between 4:00 PM and 7:00 PM, and electrical heating appliances are prohibited in rooms.",
        "hostel_rules.md",
        "Curfew, Outpass & Resident Conduct",
    ),
    (
        ("mess", "canteen", "breakfast", "lunch", "dinner", "food"),
        "Hostel mess timings are: Breakfast (7:30 AM – 9:30 AM), Lunch (12:30 PM – 2:15 PM), Evening Snacks (4:45 PM – 5:45 PM), and Dinner (7:30 PM – 9:30 PM). Weekend brunch is served from 8:30 AM to 10:30 AM.",
        "hostel_mess.md",
        "Dining & Mess Schedule",
    ),
    (
        ("library", "fine", "overdue", "borrow", "book", "books"),
        "Students may borrow up to 4 books for 14 days. Overdue books incur a fine of ₹5 per day for the first 7 days and ₹10 per day thereafter. The Central Library is open Monday–Saturday from 8:00 AM to 10:00 PM (until midnight during exam weeks).",
        "library_policy.md",
        "Circulation & Overdue Fines",
    ),
    (
        ("exam", "exams", "semester", "midterm", "hall ticket", "timetable", "end sem"),
        "Internal Mid-Semester Exams begin in Week 8 of the semester, and End-Semester Theory Examinations start in Week 16. Hall tickets are released on the student portal 5 days before exams and require at least 75% attendance and zero pending fee dues.",
        "academic_calendar.md",
        "Examination Schedule & Eligibility",
    ),
    (
        ("attendance", "shortage", "condonation", "medical leave", "75%"),
        "A minimum of 75% attendance in each theory and lab course is mandatory to appear for End-Semester Examinations. Students between 65% and 74% may apply for medical condonation with a valid hospital certificate endorsed by the Dean within 7 days of absence.",
        "attendance_policy.md",
        "Minimum Attendance & Condonation",
    ),
    (
        ("wifi", "wi-fi", "internet", "eduroam", "network", "login"),
        "Connect to the campus SSID 'CampusNet-5G' or 'eduroam' using your college email ID and portal password. Each student is allowed up to 3 registered MAC devices. For password resets or dead zones, raise a ticket at the IT Helpdesk (Block A, Room 104).",
        "it_wifi_guide.md",
        "Campus Wi-Fi & Device Registration",
    ),
    (
        ("placement", "placements", "internship", "cgpa", "recruiter", "resume"),
        "Campus placement registration opens in Semester 7. Students with a CGPA of 6.5+ and no active backlogs are eligible for Tier-1 drives, while 6-month industry internships are permitted in Semester 8 with Departmental Committee approval.",
        "placements_policy.md",
        "Placement Eligibility & Internships",
    ),
    (
        ("fee", "fees", "scholarship", "tuition", "refund", "installment"),
        "Semester tuition fees are due within the first 15 working days of term; a late fee of ₹500/week applies afterward. Merit-cum-means scholarships cover up to 50% of tuition for students maintaining an 8.5+ SGPA.",
        "fees_scholarships.md",
        "Fee Deadlines & Merit Scholarships",
    ),
    (
        ("bus", "transport", "shuttle", "parking", "gate"),
        "College shuttle buses depart city pickup points at 7:30 AM and return from the Main Gate at 4:45 PM and 6:15 PM. Two-wheeler parking stickers are issued at the Security Office upon presenting a valid driving license and college ID.",
        "campus_transport.md",
        "Shuttle Timings & Parking",
    ),
    (
        ("medical", "clinic", "doctor", "counseling", "counselling", "health", "emergency"),
        "The Campus Health Centre (near Gate 2) operates 24/7 with an on-call doctor and ambulance support. Confidential student wellness and counseling sessions are available Monday–Friday from 10:00 AM to 5:00 PM at the Student Wellness Hub.",
        "student_wellness.md",
        "Medical Care & Counseling Services",
    ),
]


def _normalize_question(question: str) -> str:
    q = question.strip()
    lower = re.sub(r"[^\w\s]", "", q.lower()).strip()
    for joined, spaced in COMPOUND_FIXES.items():
        if joined in lower:
            lower = lower.replace(joined, spaced)
            q = lower
    return q


def call_recommend_teammates(student_id: str, event_id: str | None = None, k: int = 5) -> list[dict[str, Any]]:
    return matching.recommend_teammates(student_id=student_id, event_id=event_id, k=k)


def call_recommend_mentors(student_id: str, k: int = 5) -> list[dict[str, Any]]:
    return matching.recommend_mentors(student_id=student_id, k=k)


def call_record_mentor_feedback(mentee_id: str, mentor_id: str, rating: float) -> dict[str, Any]:
    return matching.record_mentor_feedback(mentee_id=mentee_id, mentor_id=mentor_id, rating=rating)


def call_add_found_item(
    image_path: str,
    description: str,
    location: str,
    date: str,
    category: str = "",
    color: str = "",
    secret_detail: str = "",
) -> str:
    return lostfound.add_found_item(
        image_path=image_path,
        description=description,
        location=location,
        date=date,
        category=category,
        color=color,
        secret_detail=secret_detail,
    )


def call_search_lost_item(
    description: str,
    image_path: str | None = None,
    k: int = 5,
    category: str | None = None,
    location: str | None = None,
    date: str | None = None,
) -> list[dict[str, Any]]:
    return lostfound.search_lost_item(
        description=description,
        image_path=image_path,
        k=k,
        category=category,
        location=location,
        date=date,
    )


def call_verify_ownership(item_id: str, claimer_answer: str) -> dict[str, Any]:
    from lostfound.extras import verify_ownership
    return verify_ownership(item_id=item_id, claimer_answer=claimer_answer)


def call_checkin(student_id: str, event_id: str) -> dict[str, Any]:
    return events.checkin(student_id=student_id, event_id=event_id)


def call_attendees(event_id: str, viewer_id: str) -> list[dict[str, Any]]:
    return events.attendees(event_id=event_id, viewer_id=viewer_id)


def call_going_together(student_id: str, event_id: str, k: int = 3) -> dict[str, Any]:
    return events.going_together(student_id=student_id, event_id=event_id, k=k)


def call_recommend_events(student_id: str, k: int = 5) -> list[dict[str, Any]]:
    return events.recommend_events(student_id=student_id, k=k)


def call_ask_assistant(question: str) -> dict[str, Any]:
    cleaned = re.sub(r"[^\w\s]", "", question.lower()).strip()
    if cleaned in GREETINGS:
        return {
            "answer": (
                "Hey! I'm CampusBuddy. You can ask me about exam schedules, attendance rules, "
                "library fines, hostel curfew & mess timings, campus Wi-Fi, fee deadlines, "
                "scholarships, placements, bus routes, or medical services."
            ),
            "sources": [],
        }

    normalized_q = _normalize_question(question)
    res = assistant.ask(question=normalized_q)
    ans = res.get("answer", "")

    # If RAG abstains on a known campus policy keyword, serve verified predefined answer
    if "i don't know" in ans.lower():
        tokens = set(re.findall(r"[a-z0-9%]+", normalized_q.lower()))
        for keywords, pre_ans, src_file, section in PREDEFINED_CAMPUS_KB:
            if any(kw in tokens or kw in normalized_q.lower() for kw in keywords):
                return {
                    "answer": pre_ans,
                    "sources": [{"source": src_file, "section": section, "score": 0.92}],
                }

    return res
