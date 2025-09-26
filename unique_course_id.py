import json

with open("json/sjsu_majors.json", "r") as f:
    data = json.load(f)


list_of_unique_words = []

for i in range(0,len(data)):

    lowercase_file_name = data[i]["major"].lower().replace(" ", "_")
    # print(lowercase_file_name)

    with open("json/roadmaps/"+str(lowercase_file_name)+".json", "r") as r:
        read_contents = json.load(r)["output"][0]["name"]
        
        
        if type(read_contents) == list:
            for x in range(0,len(read_contents)):
                #print(read_contents[x])
                if "||" in read_contents[x]:
                    read_contents[x] = read_contents[x][2:]
                    for y in range(0, len(read_contents[x:])):
                        if read_contents[y] in list_of_unique_words:
                            pass
                        else:
                            list_of_unique_words.append(read_contents[y])

                    #print("OR:   " , read_contents[x:])
            
        
        else:
            #print("TYPE STRING:   "+read_contents)
            if read_contents in list_of_unique_words:
                pass
            else:
                list_of_unique_words.append(read_contents)


#print(list_of_unique_words)


with open("json/ge_courses.json", "r") as ge:
    courses = json.load(ge)


ge_courses_list = []


for i in range(0, len(courses)):
    if type(courses[i]["course"]) == list:
        for z in courses[i]["course"]:
            if z in ge_courses_list:
                pass
            else:
                ge_courses_list.append(z)
                # print(z)
    
    else:
        if courses[i]["course"] in ge_courses_list:
            pass
        else:
            ge_courses_list.append(courses[i]["course"])
            # print(courses[i]["course"])

print()
print()

#print(ge_courses_list)

final_unknown_areas = []


for j in range(0, len(list_of_unique_words)):
    if list_of_unique_words[j] in ge_courses_list:
        pass
    else:
        final_unknown_areas.append(list_of_unique_words[j])

print(final_unknown_areas)