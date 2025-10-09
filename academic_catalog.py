import json
from bs4 import BeautifulSoup
from ai_model import *
import requests
import time


class AcademicCatalog:
    def __init__(self, filename):
        with open(filename, "r") as f:
            self.data = json.load(f)
        
    def academic_catalog_to_file(self):
        GENERATE = AIModel()
        
        for i in range(0, len(self.data)):
            link_url = self.data[i]["link"]
            lowercase_file_name = self.data[i]["major_name"]

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
            }
            
            response = requests.get(link_url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to retrieve page: {link_url} with status code {response.status_code}")
                continue

            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")
            td = soup.find("td", colspan="4", class_="width")

            if td:
                output = td.get_text(separator="\n", strip=True)
            else:
                output = ""

            if not output.strip():
                print(f"Warning: empty scraped content for {lowercase_file_name}, skipping.")
                continue

            with open("prompts/academic_catalog_prompt.txt", "r") as txt:
                content = txt.read()
            try:
                GENERATE.call_model(
                    system_prompt=str(content), 
                    message=str(output), 
                    api_key_val="THIRD_API_KEY",
                    filename="json/academic_catalog/"+str(lowercase_file_name)+".json"
                )
            except json.JSONDecodeError as e:
                print(f"JSON decode error for {lowercase_file_name}: {e}")
                continue

            print("FINISHED: " + "json/academic_catalog/"+str(lowercase_file_name)+".json")
            time.sleep(2)


call = AcademicCatalog("json/academic_catalog.json")
call.academic_catalog_to_file()
