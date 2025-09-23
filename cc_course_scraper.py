from bs4 import BeautifulSoup
import requests
import re
from ai_model import *


class CCCourseScraper:
    
    def remove_html_tags_re(self, text):
        clean = re.compile('<.*?>')
        return re.sub(clean, ' ', text)

    def find_articulation_table(self, url):
        URL = url

        page = requests.get(URL)

        soup = BeautifulSoup(page.content, "html.parser")

        tables = soup.find_all("table", {"class": "info-table"})
        return (self.remove_html_tags_re(str(tables[1])))


#scrape = CCCourseScraper()
#a = scrape.find_articulation_table("https://transfer.sjsu.edu/web-dbgen/artic/EVERGREEN/course-to-course.html")
#print(a)