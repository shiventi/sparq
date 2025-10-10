# sparq Progress

## OCT 9, 2025
- Added Docker configuration (Dockerfile, docker-compose.yml, .dockerignore) for containerized deployment
- Fixed requirements.txt by removing built-in modules (json, re) that don't need installation
- Created an initial course recommendation engine inside app.py

## OCT 8, 2025
- Cleaned up notes.txt to remove duplicates
- Added academic_catalog.py to generate the JSON version of academic catalogs
- Created academic_catalog_prompt.txt which has the AI prompt instruction
- Made academic_catalog.json which has a list of majors that have an academic catalog
- Wrote future.md for future plans as simple bullet points

## OCT 7, 2025
- Finished adding all courses to all_sjsu_courses_with_ge.json
- Finished adding all pre-req codes to notes.txt

## OCT 6, 2025
- Added even more courses to all_sjsu_courses_with_ge.json
- Added more pre-req codes to notes.txt

## OCT 3, 2025
- Added even more courses to all_sjsu_courses_with_ge.json
- Added more pre-req codes to notes.txt

## OCT 2, 2025
- Added even more courses to all_sjsu_courses_with_ge.json
- Added more pre-req codes to notes.txt


## OCT 1, 2025
- Added more courses to all_sjsu_courses_with_ge.json
- Added more pre-req codes to notes.txt

## SEPT 30, 2025
- Added more courses to all_sjsu_courses_with_ge.json
- Added more pre-req codes to notes.txt

## SEPT 29, 2025
- Created all_sjsu_courses_with_ge.json to create a list of all SJSU course with what prereq's and GE's are needed along with what credit it fills.
- Created notes.txt to have a simple list of all requirements needed for taking course. (work-in progress)

## SEPT 27, 2025
- Created american_institutions.json to add additional courses and their requirments.
- Added more courses to ge_courses.json and /roadmaps.
- Fixed the unique_course_id.py to make sure it properly fetches all classes and their names

## SEPT 25, 2025
- Fixed ge_courses.json to correctly include courses that satisfy multiple GE areas.
  - Updated the ge_courses.json file by changing the 'area' values from uppercase to lowercase for consistency.
- Created unique_course_id.py to see what courses have not been mapped yet.
  - Made an update to unique_course_id.py to make sure it includes the areas key in ge_courses.json
- Found all the courses that SJSU offers and saved it.
- Created extra_scripts directory to hold all console logs for easy access. 

## SEPT 24, 2025
- Updated the FourYearPlan class to get the url from the sjsu_majors.json
- Use AI model to automatically parse the classes. 
- Generated all the four year plans for all SJSU majors.
- Created ge_courses.json that has a list of all SJSU GE courses

## SEPT 23, 2025
- Added a new class (FourYearPlan) and method to get the 4 year roadmaps

## SEPT 22, 2025
- Found error in the community college course articulation scraper. 
  - Fix was as simple as changing the list index from 5 to 1
- Ran the fixed script and generated all the JSON articalation files
- Created Git Repo and pushed edits

## SEPT 21, 2025
- Finished script on community college course articulation scraper and created a AI class for simple calling
- Starting running the script

## SEPT 19, 2025
- Wrote a scraper code that found the community colleges and their links
- Started writing a script to go through each community collge and scrape table content 

## SEPT 18, 2025
- Started working on idea
- Created AP courses JSON with the requirements each AP met.