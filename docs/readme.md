**Please visit [sjsu.vercel.app](https://sjsu.vercel.app) to test sparq!**

Inside the website, you can:
- Plan your classes
- Search for classes
- View the events list

# sparq

**Plan your SJSU degree with ease.**

sparq helps SJSU students plan their classes, track progress, and find the fastest path to graduation. It combines AP scores, community college courses, and SJSU offerings to recommend the best next steps.

sparq provides a Python API and CLI for degree planning and course recommendations. Install the package from PyPI:
## Quick API Usage

Install:

```bash
pip install sparq
```

Authenticate:

```bash
sparq auth
```

Example:

```python
from sparq import Sparq
client = Sparq()  # API key auto-loaded
plan = client.plan(
	major="Computer Science",
	cc_courses=[{"code": "COMSC 075", "title": "Computer Science I", "grade": "A", "institution": "Evergreen Valley College"}],
	units_per_semester=15,
	schedule_preferences={"avoid_hours": ["8:00 AM", "8:00 PM"]}
)
print(plan)
```

Other commands:

- `sparq usage` — View API usage
- `sparq recover` — Recover lost API key
- `sparq classes` — List available SJSU classes

Features:
- Automated degree planning for SJSU
- Transfer credit support (CC, AP)
- Usage tracking & key recovery


---

For more, see `docs/documentation.md` or visit:
https://github.com/shiventi/sparq/blob/main/docs/documentation.md
