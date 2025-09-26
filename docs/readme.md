# sparq

**Helping SJSU students plan their classes, one step at a time.**

sparq is a work-in-progress web app/API designed to make planning your SJSU courses easier. By combining AP scores, community college courses, and SJSU course offerings, sparq aims to suggest the most efficient path toward graduation.

> ⚠️ **Work in Progress:** Right now, the backend is being built in Python, focusing on collecting and organizing data. The web interface and full API are not ready yet.

---

## Current Progress
- JSON dataset of all AP courses and the SJSU courses they satisfy.
- JSON dataset of community colleges and their course articulations to SJSU.
- List of SJSU majors and corresponding roadmaps for planning.
- Scrapers for course data and articulation tables are under development.

---

## Planned Features
- Suggest next courses based on completed AP, community college, or SJSU courses.
- Visualize a roadmap toward degree completion.
- Provide an API for easy integration with web or mobile frontends.

---

## Getting Started (For Developers)
You can explore the data and scrapers locally. Python is the only backend requirement so far.

```bash
git clone https://github.com/shiventi/sparq.git
cd sparq
pip install -r requirements.txt
