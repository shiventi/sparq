import requests
from bs4 import BeautifulSoup
import re
import json

def remove_html_tags_re(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

URL = "https://transfer.sjsu.edu/web-dbgen/artic/all-course-to-course.html"

page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")

tables = soup.find_all("table")
a_list = []

for a in tables:
    a_values = a.find_all("a")
    a_list.append(a_values)

finished_a_text_list = []

for i in range(0, 1000):
    try:
        a_values = a.find_all("a")[i]
        #print(a_values)
        a_values = str(a_values)
        href_match = re.search(r'href=["\'](.*?)["\']', a_values)
        if href_match:
            href = href_match.group(1)
            print(href) 
        a_values = remove_html_tags_re(a_values)
        finished_a_text_list.append({"name": a_values, "link":"https://transfer.sjsu.edu"+href})
        #print(a_values)


    except:
        break
    
with open("cc_names.json", "w", encoding='utf-8') as f:
    json.dump(finished_a_text_list, f, indent=4)

#cc_names = soup.find_all("div", class_="card-content")

#print(results)