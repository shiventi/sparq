# sparq

**Plan your SJSU degree with ease.**

sparq helps SJSU students plan their classes, track progress, and find the fastest path to graduation. It combines AP scores, community college courses, and SJSU offerings to recommend the best next steps.


## API & PyPI Package

sparq provides a Python API and CLI for degree planning and course recommendations. Install the package from PyPI:

[![PyPI version](https://img.shields.io/pypi/v/sparq.svg)](https://pypi.org/project/sparq)

```bash
pip install sparq
```

### Authentication & API Key Management

To use the API, you need to authenticate and get your API key:

```bash
sparq auth
```

This command will prompt you for your email and send a 6-digit verification code to that email. Enter the code to complete authentication. Your API key will be saved locally on your device.

Once authenticated, you can use the Python API:

```python
from sparq import Sparq
client = Sparq()  # Uses locally saved API key
plan = client.plan(major="Computer Science", units_per_semester=15)
print(plan)
```

Or, you can provide the API key directly:

```python
from sparq import Sparq
client = Sparq(api_key="YOUR_API_KEY")
plan = client.plan(major="Computer Science", units_per_semester=15)
print(plan)
```

### Key Recovery

If you lose your API key, recover it with:

```bash
sparq recover
```

This will ask for your email, send a 6-digit verification code, and show your API key (which will also be saved locally).

### Usage Tracking

To view your API usage and call history:

```bash
sparq usage
```

This shows how many times you've called the API and a brief history of your calls.


## Features
- Degree planning API for SJSU students
- User authentication and email verification
- API key management and recovery
- Usage tracking and statistics

## Getting Started (For Developers)
You can explore the data and scrapers locally. Python is the only backend requirement so far.

```bash
git clone https://github.com/shiventi/sparq.git
cd sparq
pip install -r requirements.txt
