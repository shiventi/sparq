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

class FourYearPlan:
    def remove_html_tags_re(self, text):
        clean = re.compile(r'<.*?>')
        text = re.sub(clean, ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def find_four_year_plan(self, url):
        URL = url

        page = requests.get(URL)

        soup = BeautifulSoup(page.content, "html.parser")

        tables = soup.find_all("div", {"class": "custom_leftpad_20"})
        #return str(tables)
        return (self.remove_html_tags_re(str(tables)))

#scrape = FourYearPlan()
#a = scrape.find_four_year_plan("https://catalog.sjsu.edu/preview_program.php?catoid=17&poid=15699&returnto=7889")
#print(a)