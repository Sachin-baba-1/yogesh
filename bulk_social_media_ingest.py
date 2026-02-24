import os
import django
import random
import time
import sys
from django.utils import timezone

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Post, Location
from api.tasks import update_location_aggregates, extract_severity_and_class, get_real_coordinates_from_nominatim

# 60 Indian cities to scatter data
INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune", "Hyderabad", "Ahmedabad", "Jaipur", "Surat",
    "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara",
    "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut", "Rajkot", "Kalyan-Dombivli", "Vasai-Virar", "Varanasi",
    "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", "Navi Mumbai", "Allahabad", "Howrah", "Ranchi", "Gwalior", "Jabalpur",
    "Coimbatore", "Vijayawada", "Jodhpur", "Madurai", "Raipur", "Kota", "Guwahati", "Chandigarh", "Solapur", "Hubli-Dharwad",
    "Bareilly", "Moradabad", "Mysore", "Gurgaon", "Aligarh", "Jalandhar", "Tiruchirappalli", "Bhubaneswar", "Salem", "Warangal"
]

PLATFORMS = ['Instagram', 'Twitter', 'Threads']

# Templates for generating textual events
TEMPLATES = [
    "A shocking case of {threat} reported late at night near the outskirts of {city}. Be careful.",
    "Police in {city} have arrested a person related to ongoing {threat} complaints in the local market.",
    "Multiple witnesses in {city} claim a suspicious individual was {threat} people around the station.",
    "Hearing scary stories of {threat} from {city}. People should stay safe and alert!",
    "Just read a very unsettling post about {threat} happening in {city} right now.",
    "There's an aggressive mob causing panic and {threat} around the {city} area.",
    "Stay away from the downtown {city} area, reports of major {threat} ongoing.",
    "Is it true what they are saying about the {threat} incident in {city} yesterday?",
    "A girl narrowly escaped a {threat} situation in {city}. Heartbreaking.",
    "Heavy police deployment in {city} due to escalating {threat} warnings.",
    "Safe patrols have increased in {city}, feeling much {safe} walking at night now.",
    "The cops in {city} handled that dispute really well. It is very {safe} right now.",
    "Just walked back through {city}, completely {safe} and quiet.",
    "Community safety initiatives in {city} making the streets feel very {safe}.",
    "The new {safe} zones established by {city} authorities are a relief.",
    "A minor argument in {city} escalated quickly. Everyone is okay, just rattled.",
    "Traffic and loud noise in {city}. Nothing unusual.",
    "Just another busy Friday night in {city}."
]

THREATS = ['assault', 'harassment', 'stalking', 'chhedkhani', 'abduction', 'hammer attacks', 'gundagardi']
SAFES = ['safe', 'surakshit', 'secure', 'protected']

def generate_mock_data():
    data = []
    # 20 posts per platform
    for platform in PLATFORMS:
        # Pick 20 unique cities for this platform
        selected_cities = random.sample(INDIAN_CITIES, 20)
        for city in selected_cities:
            template = random.choice(TEMPLATES)
            
            # Populate text based on template
            if '{threat}' in template:
                text = template.format(city=city, threat=random.choice(THREATS))
            elif '{safe}' in template:
                text = template.format(city=city, safe=random.choice(SAFES))
            else:
                 text = template.format(city=city)
                 
            # Generate fake URL based on platform
            if platform == 'Instagram':
                 url = f"https://www.instagram.com/p/mock_{city[:3]}_{random.randint(100,999)}/"
            elif platform == 'Twitter':
                 url = f"https://twitter.com/user/status/mock_{city[:3]}_{random.randint(1000,9999)}"
            else:
                 url = f"https://www.threads.net/@user/post/mock_{city[:3]}_{random.randint(10,99)}"
                 
            data.append({"platform": platform, "url": url, "text": text, "city": city})
    return data

def main():
    print("Initializing Multi-Platform Bulk Scraper (Simulated)...")
    print("Targeting: Instagram, Twitter, Threads (20 posts each)")
    print("-" * 50)
    
    mock_scraped_data = generate_mock_data()
    
    # Shuffle so platforms interleave
    random.shuffle(mock_scraped_data)
    
    success_count = 0
    
    for item in mock_scraped_data:
        platform = item['platform']
        url = item['url']
        text = item['text']
        city_focused = item['city']
        
        # 1. Analyze NLP Context
        severity, classification = extract_severity_and_class(text)
        
        # 2. Get Geocoding
        # We know the city from our generation script, but let's pass it to Nominatim to get real India coordinates
        # to ensure it maps exactly like a real user extracting text
        display_name, lat, lon = get_real_coordinates_from_nominatim(city_focused)
        
        if lat and lon:
            # 3. Save Post
            post, created = Post.objects.get_or_create(
                source_id=url,
                defaults={
                    'source': f'{platform.lower()}_bulk_scrape',
                    'text': text[:1000],
                    'classification': classification,
                    'severity': severity,
                    'geo_lat': lat,
                    'geo_lon': lon,
                    'created_at': timezone.now(),
                    'metadata_json': {'extracted_location': display_name or city_focused, 'platform': platform}
                }
            )
            
            # 4. Update Map DB (Location / LocationAggregates)
            if created or post:
                 update_location_aggregates(post)
                 
            print(f"[{platform}] Analyzed Link: {url}")
            print(f" -> Found Location: {display_name or city_focused} | Classification: {classification.upper()} (Score: {severity})")
            print(f" -> Success! Directly Updated Live Heatmap @ {lat}, {lon}\n")
            success_count += 1
            
            # Add small sleep to not completely murder the free Nominatim API rate limits
            time.sleep(1) 
        else:
            print(f"[{platform}] Failed to geocode {city_focused} from {url}\n")
            
    print("-" * 50)
    print(f"Finished bulk analysis. Successfully mapped {success_count}/60 new social media incidents across India!")

if __name__ == "__main__":
    main()
