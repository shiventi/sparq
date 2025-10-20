from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from app import recommendation_engine, render_report


AVAILABLE_SCHEDULE_PREFERENCES: Dict[str, str] = {
    "enabled": "Toggle all schedule filtering logic.",
    "earliest_start": "Minutes from midnight or time string for first class start.",
    "latest_end": "Minutes from midnight or time string for last class end.",
    "required_day_patterns": "Exact meeting patterns (e.g., 'MW', 'TR') that must match.",
    "allowed_day_patterns": "List of acceptable meeting patterns.",
    "avoid_day_patterns": "Meeting patterns to exclude (e.g., 'F').",
    "preferred_day_patterns": "Patterns to boost during scoring.",
    "required_days": "Set of day letters that must be included (e.g., {'M', 'W'}).",
    "preferred_days": "Days to prioritize when scoring sections.",
    "avoid_days": "Days to down-rank (e.g., {'F'}).",
    "only_days": "Restrict sections to this day set exactly.",
    "allowed_instruction_modes": "Modes like 'in-person', 'online', 'hybrid' to allow.",
    "avoid_instruction_modes": "Instruction modes to exclude.",
    "allowed_section_types": "Section types to allow such as 'lecture' or 'lab'.",
    "avoid_section_types": "Section types to exclude.",
    "preferred_instructors": "Map of course code to instructor list to favor.",
    "avoid_instructors": "Map of course code to instructor list to avoid.",
    "instructor_ratings": "Mapping of instructor name to numeric rating boost.",
    "prefer_open_sections": "If true, open seats get a bonus.",
}


def _format_section_details(selection: Dict[str, Any], course: Dict[str, Any]) -> str:
    if selection.get("status") != "matched" or not selection.get("section"):
        message = selection.get("message", "No matching section found.")
        # Show suggested courses if available
        suggested = course.get("suggested_courses", [])
        if suggested:
            # Format suggested courses nicely
            course_list = ", ".join(suggested[:5])
            if len(suggested) > 5:
                course_list += ", ..."
            return f"{message} | Try: {course_list}"
        return message
    section = selection["section"]
    parts = []
    label = section.get("section") or section.get("class_number")
    if label:
        parts.append(f"Section {label}")
    instructor = section.get("instructor")
    if instructor:
        parts.append(f"Instructor: {instructor}")
    schedule_bits = [bit for bit in (section.get("days"), section.get("times")) if bit]
    if schedule_bits:
        parts.append(f"Meets: {' '.join(schedule_bits)}")
    location = section.get("location")
    if location:
        parts.append(f"Location: {location}")
    open_seats = section.get("open_seats")
    if open_seats is not None:
        parts.append(f"Open Seats: {open_seats}")
    score = section.get("score")
    if score is not None:
        parts.append(f"Fit Score: {score}")
    notes = section.get("notes")
    if notes:
        parts.append(notes)
    return " | ".join(parts) if parts else "Matched section details unavailable."


def _iter_course_entries(plan: Iterable[Dict[str, Any]]):
    for term in plan:
        yield term, term.get("courses", [])


def print_schedule_overview(plan: Iterable[Dict[str, Any]]) -> None:
    print("\n================ Section Snapshot ================")
    for term, courses in _iter_course_entries(plan):
        term_label = term.get("term", "Term")
        units = term.get("total_units", 0)
        print(f"{term_label} — {units} units")
        if not courses:
            print("  (No courses planned)")
            continue
        for course in courses:
            course_code = course.get("course") or course.get("title") or "Course"
            title = course.get("title")
            info = f"{course_code}" if course_code == title or not title else f"{course_code} – {title}"
            units = course.get("units")
            print(f"  • {info} ({units} units)")
            
            # Show suggested courses for GE requirements and electives
            if course.get("type") in ("ge", "elective"):
                suggested = course.get("suggested_courses", [])
                if suggested:
                    # Clean up course codes (remove leading || or &&)
                    cleaned = [c.lstrip("|&").strip() for c in suggested]
                    course_list = ", ".join(cleaned[:5])
                    if len(cleaned) > 5:
                        course_list += ", ..."
                    print(f"      Options: {course_list}")
                continue
            
            if course.get("type") != "course":
                continue
            
            # Show alternatives if available
            alternatives = course.get("alternatives")
            if alternatives:
                alt_list = ", ".join(alternatives)
                print(f"      Alternatives: {alt_list}")
            
            selection = course.get("section_selection") or {}
            detail = _format_section_details(selection, course)
            print(f"      {detail}")
        print("")


def _parse_time_to_minutes(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    cleaned = text.replace(" ", "").upper()
    formats = ("%I:%M%p", "%I%p", "%H:%M", "%H")
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.hour * 60 + dt.minute
        except ValueError:
            continue
    try:
        float_val = float(text)
    except ValueError:
        return None
    minutes = int(round(float_val * 60 if float_val <= 24 else float_val))
    return max(0, min(24 * 60, minutes))


def _ensure_minutes(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        minutes = int(round(value))
        return max(0, min(24 * 60, minutes))
    return _parse_time_to_minutes(value)


def _apply_avoid_hours(preferences: Dict[str, Any]) -> None:
    avoid_hours: List[Any] = list(preferences.pop("avoid_hours", []) or [])
    if not avoid_hours:
        return

    earliest = _ensure_minutes(preferences.get("earliest_start"))
    latest = _ensure_minutes(preferences.get("latest_end"))

    for entry in avoid_hours:
        minutes = _parse_time_to_minutes(entry)
        if minutes is None:
            continue
        if minutes <= 12 * 60:  # morning slot, nudge start later
            candidate = min(24 * 60, minutes + 60)
            earliest = candidate if earliest is None else max(earliest, candidate)
        if minutes >= 18 * 60:  # evening slot, nudge end earlier
            candidate = max(0, minutes - 60)
            latest = candidate if latest is None else min(latest, candidate)

    if earliest is not None:
        preferences["earliest_start"] = earliest
    if latest is not None:
        preferences["latest_end"] = latest


def _prepare_schedule_preferences(profile: Dict[str, Any]) -> None:
    preferences = profile.get("schedule_preferences")
    if not isinstance(preferences, dict):
        return
    _apply_avoid_hours(preferences)


def main() -> None:
    sample_student = {
    "major": "Computer Science",
    "cc_courses": [
        # EVC Courses (based on actual transcript)
        {"code": "COMSC 075", "title": "Computer Science I", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "COMSC 076", "title": "Computer Science II", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "COMS 020", "title": "Oral Communication", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "ART 096", "title": "History of Asian Art", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "COMS 035", "title": "Intercultural Communication", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "PSYCH 001", "title": "General Psychology", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "PHIL 060", "title": "Logic and Critical Thinking", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "PHIL 010", "title": "Introduction to Philosophy", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "PHIL 065", "title": "Introduction to Ethics", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "COMSC 080", "title": "Discrete Structures", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "HIST 017A", "title": "History of the United States", "grade": "A", "institution": "Evergreen Valley College"},
        # SJCC Courses
        {"code": "ENGL 001A", "title": "English Composition", "grade": "A", "institution": "San Jose City College"},
    ],
    "ap_exams": [
        {"test": "Calculus AB", "score": 5},
        {"test": "Calculus BC", "score": 4},
        {"test": "World History", "score": 4},
    ],
    "sjsu_courses": [
        {"code": "MATH 32", "title": "Calculus III", "status": "In Progress", "term": "Fall 2025"},
        {"code": "CS 49J", "title": "Programming in Java", "status": "In Progress", "term": "Fall 2025"},
        {"code": "NUFS 16", "title": "Nutrition", "status": "In Progress", "term": "Fall 2025"},
        {"code": "METR 10", "title": "Weather and Climate", "status": "In Progress", "term": "Fall 2025"},
    ],
    "units_per_semester": 16,
    "schedule_preferences": {
        "enabled": True,
        "avoid_hours": ["8:00 AM", "8:00 PM"],
        "prefer_open_sections": True,
    },
}

    _prepare_schedule_preferences(sample_student)
    summary, plan, semesters = recommendation_engine(sample_student)
    # render_report returns a human-readable string
    report = render_report(summary, plan, semesters)
    print(report)
    print_schedule_overview(plan)


if __name__ == "__main__":
    main()
