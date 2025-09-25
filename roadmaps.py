import json
from bs4 import BeautifulSoup
import re
from ai_model import *
import requests
import time
from scraper import *

class Roadmap:
    def __init__(self, filename):
        with open(filename, "r") as f:
            self.data = json.load(f)
        
    def roadmaps_to_file(self):
        GENERATE = AIModel()
        
        for i in range(0, len(self.data)):
            link_url = self.data[i]["link"]
            lowercase_file_name = self.data[i]["major"].lower().replace(" ", "_")
            scrape = FourYearPlan()
            output = scrape.find_four_year_plan(link_url)
            
            # print()
            # print()
            # print(lowercase_file_name.upper())
            # print()
            # print()
            # print()
            # print()
            # print(output)



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

            with open("prompts/four_year_roadmap.txt", "r") as txt:
                content = txt.read()
                
            GENERATE.call_model(
            system_prompt=str(content), 
            message=output, 
            api_key_val="SECOND_API_KEY",
            filename="json/roadmaps/"+str(lowercase_file_name)+".json")

            
            print("FINISHED: " + "json/"+str(lowercase_file_name)+".json")
            time.sleep(2)
            # print(current_content_string)
            # print(lowercase_file_name)
            # print()
            # print()
            # print()
            # print()
            # print()
            # print()

        





call = Roadmap("json/sjsu_majors.json")
call.roadmaps_to_file()
