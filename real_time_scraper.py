import os
import django
import sys
import time
from django.utils import timezone

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Post
from api.tasks import update_location_aggregates, extract_severity_and_class, get_real_coordinates_from_nominatim
from playwright.sync_api import sync_playwright

def scrape_search_results():
    """
    Uses headless Chromium to search standard aggregators (Google/Bing) for recent 
    news about safety in Indian cities to pull real dynamic titles/snippets.
    """
    search_queries = [
        "latest women safety news India",
        "recent harassment cases Delhi",
        "safe neighborhoods Bangalore news",
        "Mumbai night time safety update",
        "violent incident Hyderabad news"
    ]
    
    scraped_data = []

    print("Launching Headless Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for query in search_queries:
            try:
                print(f"[{timezone.now()}] Scraping real search data for: '{query}'")
                # Using Bing as it is often less aggressive with captchas for headless browsers than Google
                page.goto(f"https://www.bing.com/news/search?q={query}")
                page.wait_for_selector(".news-card", timeout=10000)
                
                # Extract text from the loaded news cards
                cards = page.query_selector_all(".news-card")
                for card in cards[:3]: # grab top 3 results per query
                    title_elem = card.query_selector(".title")
                    snippet_elem = card.query_selector(".snippet")
                    
                    title = title_elem.inner_text() if title_elem else ""
                    snippet = snippet_elem.inner_text() if snippet_elem else ""
                    link = title_elem.get_attribute("href") if title_elem else f"playwright://search/{query}_{time.time()}"
                    
                    if title and snippet:
                        text = f"{title}. {snippet}"
                        scraped_data.append({"url": link, "text": text})
            except Exception as e:
                 print(f"Error scraping query '{query}': {e}")
                 
        browser.close()
        
    return scraped_data

def main():
    print("Initializing Real-Time Headless Scraper...")
    print("-" * 50)
    
    live_data = scrape_search_results()
    print(f"Successfully extracted {len(live_data)} real, live reports from search aggregators.")
    print("Routing to NLP Pipeline and OpenStreetMap Geocoder...")
    print("-" * 50)
    
    success_count = 0
    
    for item in live_data:
        url = item['url']
        text = item['text']
        
        # 1. Analyze NLP Context
        severity, classification = extract_severity_and_class(text)
        
        # 2. Extract City Name for Geocoding
        # We'll do a quick scan against our basic known cities, or fallback if unknown
        INDIAN_CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Ahmedabad', 'Chennai', 'Kolkata', 'Pune', 'Jaipur', 'Noida', 'Gurugram']
        found_city = None
        for city in INDIAN_CITIES:
            if city.lower() in text.lower():
                found_city = city
                break
                
        if found_city:
            # Send to OSM for true lat/lon
            display_name, lat, lon = get_real_coordinates_from_nominatim(found_city)
            
            if lat and lon:
                post, created = Post.objects.get_or_create(
                    source_id=url,
                    defaults={
                        'source': 'playwright_live_scrape',
                        'text': text[:1000],
                        'classification': classification,
                        'severity': severity,
                        'geo_lat': lat,
                        'geo_lon': lon,
                        'created_at': timezone.now(),
                        'metadata_json': {'extracted_location': display_name or found_city}
                    }
                )
                
                # Update Map DB
                if created or post:
                     update_location_aggregates(post)
                     
                print(f"[Real Data] Mapped {url}")
                print(f" -> Found City: {found_city}")
                print(f" -> Classification: {classification.upper()} (Score: {severity})")
                print(f" -> True Coordinates: {lat}, {lon}\n")
                success_count += 1
                time.sleep(1) # throttle Nominatim
        else:
             print(f"Skipping: Could not reliably identify an Indian city for mapping in text: '{text[:50]}...'\n")

    print("-" * 50)
    print(f"Finished real-time scraping. Successfully mapped {success_count}/{len(live_data)} live items to the Map Engine!")

if __name__ == "__main__":
    main()
