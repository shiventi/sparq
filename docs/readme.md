# sparq

**Plan your SJSU degree with ease.**

sparq helps SJSU students plan their classes, track progress, and find the fastest path to graduation. It combines AP scores, community college courses, and SJSU offerings to recommend the best next steps.

## API & PyPI Package

sparq now provides a Python API for degree planning and course recommendations. Install the package from PyPI:

[![PyPI version](https://img.shields.io/pypi/v/sparq.svg)](https://pypi.org/project/sparq)

```bash
pip install sparq
```

Example usage:
```python
from sparq import Sparq
client = Sparq(api_key="YOUR_API_KEY")
plan = client.plan(major="Computer Science", units_per_semester=15)
print(plan)
```

## Features
- Degree planning API for SJSU students
- User authentication and API key management
- Usage tracking and statistics
- Email verification (Brevo integration)
- JSON datasets for AP, community college, and SJSU courses
- Scrapers for course and articulation data

## Getting Started (For Developers)
You can explore the data and scrapers locally. Python is the only backend requirement so far.

```bash
git clone https://github.com/shiventi/sparq.git
cd sparq
pip install -r requirements.txt
