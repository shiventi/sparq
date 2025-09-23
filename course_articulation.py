import json
from bs4 import BeautifulSoup
import re
from ai_model import *
import requests
import time
from cc_course_scraper import *

class CourseArticulationJSON:
    def __init__(self, filename):
        with open(filename, "r") as f:
            self.data = json.load(f)

        
    def course_aritculation_to_file(self):
        CALL_AI_MODEL = AIModel()
        
        for i in range(0, len(self.data)):
            link_url = self.data[i]["link"]
            lowercase_file_name = self.data[i]["name"].lower().replace(" ", "_")
            scrape = CCCourseScraper()
            output = scrape.find_articulation_table(link_url)
            #print(output)



            # URL = link_url
            # page = requests.get(URL)
            # soup = BeautifulSoup(page.content, "html.parser")
            # course_to_course = soup.find_all("tr")
            # current_content_string = ""
            
        
            # for y in range(0,len(course_to_course)):
            #     if "valign=" in str(course_to_course[y]):
            #         start_value = y
            #         break
                

            # for x in range(i, len(course_to_course)):
            #     soup = BeautifulSoup(str(course_to_course[x]), "html.parser")
            #     for td in soup.find_all("td"):
            #         current_content_string+=td.get_text(strip=True) + "\n"
            #         #print(td.get_text(strip=True))

            # #with open("json/"+str(lowercase_file_name)+".json", "w") as j:

            with open("prompts/course_articulation_prompt.txt", "r") as txt:
                content = txt.read()
                
                
            CALL_AI_MODEL.call_model(
            system_prompt=str(content), 
            message=output, 
            filename="json/community_college/"+str(lowercase_file_name)+".json")

                


            
            print("FINISHED: " + "json/"+str(lowercase_file_name)+".json")
            time.sleep(10)
            # print(current_content_string)
            # print(lowercase_file_name)
            # print()
            # print()
            # print()
            # print()
            # print()
            # print()

        





call = CourseArticulationJSON("json/cc_names.json")
call.course_aritculation_to_file()
