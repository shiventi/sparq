import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import json
from aiohttp import ClientSession

class EventScraper:
    
    def remove_html_tags_re(self, text):
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).replace('\u00a0', ' ').replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"').replace('\n', ' ').strip()

    async def fetch_page(self, session: ClientSession, url: str) -> str:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                print(f"Failed to fetch {url}: Status {response.status}")
                return ""
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""

    async def fetch_event_details(self, session: ClientSession, event: dict) -> dict:
        """Fetch additional details from the event's detail page."""
        if not event.get('link'):
            return event
        
        page_content = await self.fetch_page(session, event['link'])
        if not page_content:
            return event
        
        soup = BeautifulSoup(page_content, 'lxml')  # Use lxml for faster parsing
        
        # Target Audience
        audience_div = soup.find("div", class_=re.compile(r".*audience.*", re.I))
        if audience_div:
            audience = [item.get_text().strip() for item in audience_div.find_all(["li", "a"]) if item.get_text().strip()]
            if audience:
                event['target_audience'] = audience
        
        # Performance Type
        perf_type_div = soup.find("div", class_=re.compile(r".*performance.*", re.I))
        if perf_type_div:
            perf_type = perf_type_div.get_text().strip()
            if perf_type:
                event['performance_type'] = perf_type
        
        # Interested Attendees
        interested_div = soup.find("div", class_=re.compile(r".*interested.*", re.I))
        if interested_div:
            interested = interested_div.get_text().strip()
            if interested:
                event['interested'] = interested
        
        # Department
        dept_div = soup.find("div", class_=re.compile(r".*department.*", re.I))
        if dept_div:
            dept = dept_div.get_text().strip()
            if dept:
                event['department'] = dept
        
        return event

    async def find_events(self, session: ClientSession, url: str) -> list:
        page_content = await self.fetch_page(session, url)
        if not page_content:
            return []
        
        soup = BeautifulSoup(page_content, 'lxml')  # Use lxml for faster parsing
        events = []
        
        card_groups = soup.find_all("div", class_="em-card-group")
        for group in card_groups:
            day_header = group.find_previous_sibling("h2", class_="em-content-label")
            day = day_header.get_text().strip() if day_header else None
            
            cards = group.find_all("div", class_="em-card")
            for card in cards:
                event = {}
                
                # Only add day if it exists and is not empty
                if day and day != "Unknown Date":
                    event['day'] = day
                
                # Extract from ld+json
                script = card.find_previous_sibling("script", type="application/ld+json")
                if script:
                    try:
                        data = json.loads(script.contents[0])[0]
                        if name := data.get('name', '').strip():
                            event['title'] = name
                        if description := self.remove_html_tags_re(data.get('description', '')):
                            event['description'] = description
                        if start_date := data.get('startDate'):
                            event['start_date'] = start_date
                        if end_date := data.get('endDate'):
                            event['end_date'] = end_date
                        if url := data.get('url'):
                            event['url'] = url
                        location_data = data.get('location', {})
                        if location_data.get('@type') == 'VirtualLocation':
                            if virtual_location := 'Virtual Event':
                                event['location'] = virtual_location
                            if virtual_url := location_data.get('url'):
                                event['virtual_url'] = virtual_url
                        else:
                            if loc_name := location_data.get('name', '').strip():
                                event['location'] = loc_name
                            if address := location_data.get('address', '').strip():
                                event['address'] = address
                    except (json.JSONDecodeError, IndexError) as e:
                        print(f"Error parsing ld+json: {e}")
                
                # Extract from card
                title_tag = card.find("h3", class_="em-card_title")
                if title_tag and title_tag.a:
                    if title := title_tag.a.get_text().strip():
                        event['title'] = title
                    if link := title_tag.a.get('href'):
                        event['link'] = link
                
                event_times = card.find_all("p", class_="em-card_event-text")
                if event_times:
                    if time := event_times[0].get_text().strip():
                        event['time'] = time
                    if len(event_times) > 1:
                        loc_tag = event_times[1].find("a")
                        if loc_tag and (loc_text := loc_tag.get_text().strip()):
                            event['location'] = loc_text
                
                if card.find("i", class_="fas fa-tv"):
                    event['location'] = 'Virtual Event'
                
                tags = [a.get_text().strip() for a in card.find("div", class_="em-list_tags").find_all("a", class_="em-card_tag") if a.get_text().strip()] if card.find("div", class_="em-list_tags") else []
                if tags:
                    event['tags'] = tags
                
                price_tag = card.find("span", class_="em-price-tag")
                if price_tag and (price := price_tag.get_text().strip()):
                    event['price'] = price
                
                if event:  # Only add event if it has some data
                    events.append(event)
        
        # Fetch event details concurrently
        tasks = [self.fetch_event_details(session, event) for event in events]
        detailed_events = await asyncio.gather(*tasks, return_exceptions=True)
        return [e for e in detailed_events if not isinstance(e, Exception) and e]

    async def scrape_all_events(self, base_url: str) -> list:
        async with aiohttp.ClientSession() as session:
            events = []
            page = 1
            max_concurrent_pages = 5  # Limit concurrent page fetches to avoid server overload
            
            while True:
                # Generate batch of page URLs
                page_urls = [base_url if i == 1 else f"{base_url}/{i}" for i in range(page, min(page + max_concurrent_pages, page + 10))]
                if not page_urls:
                    break
                
                print(f"Fetching pages: {page_urls}")
                tasks = [self.find_events(session, url) for url in page_urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                page_has_events = False
                for i, result in enumerate(results):
                    if isinstance(result, list) and result:
                        events.extend(result)
                        page_has_events = True
                    elif isinstance(result, Exception):
                        print(f"Error fetching page {page + i}: {result}")
                
                if not page_has_events:
                    print(f"No events found in batch starting at page {page}, stopping.")
                    break
                
                page += len(page_urls)
                # Minimal delay to be polite, reduced from 0.5s to 0.1s
                await asyncio.sleep(0.1)
            
            return events

    def run_scrape(self, base_url: str) -> list:
        return asyncio.run(self.scrape_all_events(base_url))

# Run the scraper
if __name__ == "__main__":
    scrape = EventScraper()
    events = scrape.run_scrape("https://events.sjsu.edu/calendar")
    with open('output_events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=4, ensure_ascii=False)
    print(f"Scraped {len(events)} events.")