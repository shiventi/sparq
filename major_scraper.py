from bs4 import BeautifulSoup
import requests
import re
import json


class MajorScraper:
    
    def remove_html_tags_re(self, text):
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def clean_majors_text(self, text):
        text = re.sub(r'^\s*•\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^.*(?:2-Year|5-Year).*$\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'Roadmap:\s*', '', text)
        text = re.sub(r'\n\s*\n', '\n', text).strip()
        return text

    def find_articulation_table(self, url):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        majors = soup.find_all("ul", {"class": "program-list"})
        
        major_links = []
        for ul in majors:
            for li in ul.find_all("li"):
                a_tag = li.find("a")
                if a_tag and a_tag.get("href"):
                    link_text = a_tag.get_text().strip()
                    
                if not re.search(r'(?:2-year|3-year|5-year|2-Year|3-Year|5-Year|\(\d+-year|\d+-year\s)', link_text, re.IGNORECASE):
                    clean_text = re.sub(r'^Roadmap:\s*', '', link_text)
                    major_links.append({
                        'major': clean_text,
                        'link': "https://catalog.sjsu.edu/"+ a_tag.get("href")
                    })
        
        return major_links


scrape = MajorScraper()
a = scrape.find_articulation_table("https://catalog.sjsu.edu/content.php?catoid=17&navoid=7889")

with open('json/sjsu_majors.json', 'w') as f:
    json.dump(a, f, indent=2)
