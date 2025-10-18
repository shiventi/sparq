## Example Usage

```python
from app import recommendation_engine

sample_student = {
	"major": "Computer Science",
	"cc_courses": [
		{"code": "COMSC 075", "title": "Computer Science I", "grade": "A", "institution": "Evergreen Valley College"},
		# ... more courses ...
	],
	"ap_exams": [
		{"test": "Calculus AB", "score": 5},
		# ... more exams ...
	],
	"sjsu_courses": [
		{"code": "MATH 32", "title": "Calculus III", "status": "In Progress", "term": "Fall 2025"},
		# ... more SJSU courses ...
	],
	"units_per_semester": 16,
	"schedule_preferences": {
		"enabled": True,
		"avoid_hours": ["8:00 AM", "8:00 PM"],
		"prefer_open_sections": True,
	},
}

summary, plan, semesters = recommendation_engine(sample_student)
print(summary)
print(plan)
print(semesters)
```

## API Usage Example

```python
from sparq import Sparq

# Initialize client (API key auto-loaded from ~/.sparq/config.txt)
client = Sparq()

# Generate a degree plan
plan = client.plan(
	major="Computer Science",
	cc_courses=[
		{
			"code": "COMSC 075",
			"title": "Computer Science I",
			"grade": "A",
			"institution": "Evergreen Valley College"
		},
		# ... more courses ...
	],
	ap_exams=[
		{"test": "Calculus AB", "score": 5},
		# ... more exams ...
	],
	sjsu_courses=[
		{"code": "MATH 32", "title": "Calculus III", "status": "In Progress", "term": "Fall 2025"},
		# ... more SJSU courses ...
	],
	units_per_semester=16,
	schedule_preferences={
		"enabled": True,
		"avoid_hours": ["8:00 AM", "8:00 PM"],
		"prefer_open_sections": True,
	},
)

print(plan)
```

### Student Profile Schema

```
major: Primary declared major (string).
cc_courses: List of community college completions.
	- code: Course identifier (string).
	- title: Official course title (string).
	- grade: Earned grade or credit notation (string).
	- institution: Source institution name (string).
ap_exams: List of AP results.
	- test: Exam name (string).
	- score: Reported score (number).
sjsu_courses: List of SJSU coursework with status.
	- code: Course identifier (string).
	- title: Course title (string).
	- status: Completion status, e.g., "Completed" or "In Progress" (string).
	- term: Academic term descriptor, e.g., "Fall 2025" (string).
units_per_semester: Target load for planning (number).
schedule_preferences: Optional filters and weights for section selection (object).
```

### Schedule Preference Keys

```
enabled: Toggle all schedule filtering logic.
earliest_start: Minutes from midnight or time string for first class start.
latest_end: Minutes from midnight or time string for last class end.
required_day_patterns: Exact meeting patterns (e.g., "MW", "TR") that must match.
allowed_day_patterns: List of acceptable meeting patterns.
avoid_day_patterns: Meeting patterns to exclude (e.g., "F").
preferred_day_patterns: Patterns to boost during scoring.
required_days: Set of day letters that must be included (e.g., {"M", "W"}).
preferred_days: Days to prioritize when scoring sections.
avoid_days: Days to down-rank (e.g., {"F"}).
only_days: Restrict sections to this day set exactly.
allowed_instruction_modes: Modes like "in-person", "online", "hybrid" to allow.
avoid_instruction_modes: Instruction modes to exclude.
allowed_section_types: Section types to allow such as "lecture" or "lab".
avoid_section_types: Section types to exclude.
preferred_instructors: Map of course code to instructor list to favor.
avoid_instructors: Map of course code to instructor list to avoid.
instructor_ratings: Mapping of instructor name to numeric rating boost.
prefer_open_sections: If true, open seats get a bonus.
```
