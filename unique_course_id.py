import json

def normalize_course_name(name: str) -> str:
    # strip leading || or &&, and whitespace
    if name.startswith("||") or name.startswith("&&"):
        name = name[2:]
    return name.strip()

with open("json/sjsu_majors.json", "r") as f:
    majors = json.load(f)

list_of_unique_words = []

# build list_of_unique_words
for major in majors:
    lowercase_file_name = major["major"].lower().replace(" ", "_")
    with open(f"json/roadmaps/{lowercase_file_name}.json", "r") as r:
        roadmap = json.load(r)["output"]
        for entry in roadmap:
            names = entry.get("name", [])
            if isinstance(names, list):
                for item in names:
                    if isinstance(item, str):
                        item = normalize_course_name(item)
                        if item not in list_of_unique_words:
                            list_of_unique_words.append(item)
            elif isinstance(names, str):
                item = normalize_course_name(names)
                if item not in list_of_unique_words:
                    list_of_unique_words.append(item)

# GE areas
with open("json/ge_courses.json", "r") as ge:
    courses = json.load(ge)

ge_courses_list = []
for c in courses:
    area = c["area"]
    if isinstance(area, list):
        for a in area:
            a = normalize_course_name(a)
            if a not in ge_courses_list:
                ge_courses_list.append(a)
    else:
        a = normalize_course_name(area)
        if a not in ge_courses_list:
            ge_courses_list.append(a)

# all sjsu courses
with open("json/all_sjsu_courses.json", "r") as all_courses:
    final_file = json.load(all_courses)

# normalize the titles too
all_sjsu_courses = [normalize_course_name(c["title"]) for c in final_file]

# find unknowns
final_unknown_areas = []
for word in list_of_unique_words:
    norm_word = normalize_course_name(word)
    if norm_word in ge_courses_list:
        continue
    elif norm_word in all_sjsu_courses:
        continue
    elif norm_word in final_unknown_areas:
        continue
    else:
        final_unknown_areas.append(norm_word)

print(final_unknown_areas)
