import logging
import random
import requests
from datetime import timedelta
from django.utils import timezone
from .models import Post, Location, LocationAggregate, UserURL
import math

logger = logging.getLogger(__name__)

# Expanded Lexicon including Hindi/Regional terms for the Indian MVP context
RISKY_KEYWORDS = [
    'assault', 'threat', 'stalking', 'creep', 'following', 'harassment', 'unsafe', 'danger', 'attack', 'abduction',
    'hamla', 'chhedkhani', 'dar', 'asafe', 'khatra', 'pareshan', 'dhokha', 'picha', 'gundagardi', 'maar', 'bachao'
]
SAFE_KEYWORDS = [
    'safe', 'police', 'patrol', 'good', 'fine', 'clear', 'secure', 'protected',
    'surakshit', 'thik', 'raksha', 'mahfooz', 'shanti'
]

# Some mock Indian cities for the cron ingest to scatter data around
INDIAN_CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Ahmedabad', 'Chennai', 'Kolkata', 'Pune', 'Jaipur']

def extract_severity_and_class(text):
    text_lower = text.lower()
    
    risk_score = 0.0
    safe_score = 0.0
    
    for word in RISKY_KEYWORDS:
        if word in text_lower:
            risk_score += 0.4
            
    for word in SAFE_KEYWORDS:
        if word in text_lower:
            safe_score += 0.3
            
    # Rebalanced scoring: default to neutral, escalate on risk, recover on safe
    if risk_score > safe_score:
        classification = "threat" if risk_score >= 0.8 else "concern"
        return min(risk_score, 1.0), classification
    elif safe_score > risk_score:
        return 0.0, "safe"
        
    return 0.2, "neutral"

def get_real_coordinates_from_nominatim(location_name):
    """
    Calls OpenStreetMap Nominatim API to geocode a location string into real Lat/Lon.
    Restricted to India using the countrycodes param for better accuracy.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={location_name}&countrycodes=in&format=json&limit=1"
        headers = {'User-Agent': 'SafeSpaceAI/1.0 MVP'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]['display_name'], float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        logger.error(f"Geocoding failed for {location_name}: {e}")
        
    return None, None, None

def mock_ner_extract_location(text):
    """
    Extracts a location name from text and fetches real coordinates.
    In prod, use spaCy `doc.ents` filtering for `GPE` or `LOC` to get the name first.
    For this MVP, we simulate the extraction phase, then use real Geocoding in the second phase.
    """
    text_lower = text.lower()
    
    found_city = None
    for city in INDIAN_CITIES:
        if city.lower() in text_lower:
            found_city = city
            break
            
    if found_city:
        return get_real_coordinates_from_nominatim(found_city)
        
    return None, None, None

def process_post_nlp(post_id):
    """
    Background Task triggered when a new Post is ingested.
    """
    try:
        post = Post.objects.get(id=post_id)
        
        # 1. NLP Classification
        severity, classification = extract_severity_and_class(post.text)
        post.severity = severity
        post.classification = classification
        
        # 2. Geocoding (NER)
        if not post.geo_lat or not post.geo_lon:
            loc_name, lat, lon = mock_ner_extract_location(post.text)
            if lat and lon:
                post.geo_lat = lat
                post.geo_lon = lon
                post.metadata_json['extracted_location'] = loc_name
        
        post.save()
        logger.info(f"Processed Post {post_id}: Class={classification} Sev={severity}")
        
        # 3. Update Location Aggregates if location is known
        if post.geo_lat and post.geo_lon:
            update_location_aggregates(post)

    except Post.DoesNotExist:
        logger.error(f"Post {post_id} not found.")

def update_location_aggregates(post):
    """
    Find or create a Location cell and update its safety score.
    """
    # Create a rough 0.01 degree bounding box (~1km) for this coordinate
    min_lat = round(post.geo_lat - 0.005, 4)
    max_lat = round(post.geo_lat + 0.005, 4)
    min_lon = round(post.geo_lon - 0.005, 4)
    max_lon = round(post.geo_lon + 0.005, 4)
    
    # Find overlapping Location
    location, created = Location.objects.get_or_create(
        min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon,
        defaults={
            'name': post.metadata_json.get('extracted_location', 'Unknown Area'),
            'safety_score': 50 # Start neutral
        }
    )
    
    if post.severity > 0.3:
        # Heavily penalize the area
        location.safety_score = max(0, location.safety_score - int(post.severity * 20))
    elif post.classification == 'safe':
        # Recovery
        location.safety_score = min(100, location.safety_score + 5)
        
    location.save()

import xml.etree.ElementTree as ET

def mass_ingestion_cron():
    """
    Scheduled job to ingest real public data (like News RSS feeds) across India to populate the map continuously.
    Runs every 5 minutes.
    """
    try:
        url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        
        # Get random selection of current news items to analyze
        items = root.findall('.//item')
        random.shuffle(items)
        
        for item in items[:5]:
            title = item.find('title').text
            description_node = item.find('description')
            description = description_node.text if description_node is not None else ""
            link = item.find('link').text
            
            # Prevent duplicate ingestions
            if Post.objects.filter(source_id=link).exists():
                continue
                
            combined_text = f"{title}. {description}"
            
            post = Post.objects.create(
                source='google_news_india',
                source_id=link,
                text=combined_text,
                created_at=timezone.now()
            )
            
            # Queue for NLP processing (Severity + Geocoding)
            process_post_nlp(post.id)
            logger.info(f"Ingested real data mass link: {link}")
            
    except Exception as e:
        logger.error(f"Mass Ingestion failed: {e}")

from bs4 import BeautifulSoup

def user_url_crawler_cron():
    """
    Scheduled job designed to run every 3 hours.
    Crawls active UserURLs submitted via the frontend for new threats.
    """
    active_urls = UserURL.objects.filter(is_active=True)
    
    for user_url in active_urls:
        try:
            # Respectful scraping with basic headers
            headers = {'User-Agent': 'SafeSpaceAI/1.0 UserCrawler'}
            page = requests.get(user_url.url, headers=headers, timeout=10)
            soup = BeautifulSoup(page.content, 'html.parser')
            
            title = soup.title.string if soup.title else ""
            meta_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            meta_desc = meta_tag.get('content', '') if meta_tag else ""
            
            combined_text = f"{title}. {meta_desc}"
            
            if len(combined_text) > 20:
                # Log as a new post to trigger NLP processing automatically
                post = Post.objects.create(
                    source='user_submitted_crawler',
                    source_id=f"crawl_{user_url.id}_{timezone.now().timestamp()}",
                    text=combined_text,
                    created_at=timezone.now()
                )
                process_post_nlp(post.id)
            
            # Update Crawler Timestamp
            user_url.last_crawled = timezone.now()
            user_url.save()
            logger.info(f"Crawled UserURL {user_url.url}")
            
        except Exception as e:
            logger.error(f"Failed to crawl UserURL {user_url.url}: {e}")
