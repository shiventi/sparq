from __future__ import annotations

from app import recommendation_engine, render_report


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
    "units_per_semester": 16
}

    summary, plan, semesters = recommendation_engine(sample_student)
    # render_report returns a human-readable string
    report = render_report(summary, plan, semesters)
    print(report)


if __name__ == "__main__":
    main()
