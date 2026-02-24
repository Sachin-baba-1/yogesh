import logging
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django_q.tasks import async_task

from .models import Post, Location
from .serializers import PostSerializer, LocationSerializer
import time

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_location_score(request):
    """
    Returns safety score and associated data for a requested location (via lat/lon + radius bounding box).
    GET /api/location/score?lat={}&lon={}&radius=500
    """
    try:
        lat = float(request.GET.get('lat'))
        lon = float(request.GET.get('lon'))
        radius = float(request.GET.get('radius', 500)) / 100000.0 # very rough degrees approx for sq bounding boxes
        
        # Calculate bounding box
        min_lat = lat - radius
        max_lat = lat + radius
        min_lon = lon - radius
        max_lon = lon + radius
        
        # Find overlapping locations
        locations = Location.objects.filter(
            max_lat__gte=min_lat,
            min_lat__lte=max_lat,
            max_lon__gte=min_lon,
            min_lon__lte=max_lon
        )
        
        serializer = LocationSerializer(locations, many=True)
        
        # For MVP, we'll return an aggregated mock summary if we don't have enough data
        return Response({
            "message": "Success",
            "bounding_box": {"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon},
            "locations": serializer.data
        })
    except (TypeError, ValueError):
        return Response({"error": "Invalid parameters. Please provide float lat and lon."}, status=status.HTTP_400_BAD_REQUEST)

import requests
from bs4 import BeautifulSoup
from .tasks import extract_severity_and_class, mock_ner_extract_location, update_location_aggregates

@api_view(['POST'])
def analyze_url(request):
    """
    Perform on-demand scrape and analyze of a URL.
    POST /api/analyze-url
    Body: {"url": "https://..."}
    """
    url = request.data.get('url')
    if not url:
         return Response({"error": "URL is required."}, status=status.HTTP_400_BAD_REQUEST)
         
    # Fetch content using BeautifulSoup
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        page = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')
        
        # Extract title and meta descriptions which usually hold social post text
        title = soup.title.string if soup.title else ""
        meta_desc = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '')
            
        combined_text = f"{title}. {meta_desc}"
        if not combined_text.strip():
             combined_text = "Could not cleanly extract text from this URL due to anti-bot protection. Using fallback analysis."
             
    except Exception as e:
        logger.error(f"Scraping failed for {url}: {e}")
        combined_text = f"Simulated analysis for {url} because our scraper was blocked."

    # Run the extracted text through our NLP processors
    severity, classification = extract_severity_and_class(combined_text)
    loc_name, lat, lon = mock_ner_extract_location(combined_text)
    
    locations_extracted = []
    if loc_name:
        locations_extracted.append({"name": loc_name, "lat": lat, "lon": lon, "confidence": 0.85})

    supporting_comments = []
    if 'soup' in locals():
        # Scrape <p> tags to act as pseudo-comments for deep analysis
        paragraphs = soup.find_all('p')
        p_texts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 30 and text not in combined_text and text not in p_texts:
                p_texts.append(text)
                
        # Limit to 5 comments to analyze
        for idx, c_text in enumerate(p_texts[:5]):
            c_sev, c_class = extract_severity_and_class(c_text)
            c_loc, c_lat, c_lon = mock_ner_extract_location(c_text)
            
            supporting_comments.append({
                "id": f"comment_{idx}",
                "text": c_text[:150] + "..." if len(c_text) > 150 else c_text,
                "classification": c_class,
                "severity": c_sev
            })
            
            # If a comment reveals a new location, add it
            if c_loc and not any(loc["name"] == c_loc for loc in locations_extracted):
                locations_extracted.append({"name": c_loc, "lat": c_lat, "lon": c_lon, "confidence": 0.75})
                
            # If a comment is highly risky, drag the main severity up
            if c_sev > severity:
                severity = c_sev
                classification = c_class
                
    # Scale mathematical safety score
    if classification == "safe":
        safety_score = 90
    elif classification == "neutral":
        safety_score = 50
    else:
        safety_score = max(0, 50 - int(severity * 50))
        
    trend = "increasing risk" if severity > 0.3 else "stable"

    # PERMANENTLY MAP THE USER'S SUBMITTED THREAT TO THE DATABASE
    if url and combined_text and locations_extracted:
        # Save the primary post to trigger history
        post, created = Post.objects.get_or_create(
            source_id=url,
            defaults={
                'source': 'user_link_analyzer',
                'text': combined_text[:1000],
                'classification': classification,
                'severity': severity,
                'geo_lat': locations_extracted[0]['lat'],
                'geo_lon': locations_extracted[0]['lon'],
                'created_at': timezone.now(),
                'metadata_json': {'extracted_location': locations_extracted[0]['name']}
            }
        )
        # Update the Live Map Location Aggregates
        if created or post:
             update_location_aggregates(post)

    response_data = {
        "source_url": url,
        "post": {
            "text": combined_text[:500] + "..." if len(combined_text) > 500 else combined_text,
            "classification": classification,
            "severity": severity,
            "locations": locations_extracted,
            "supporting_comments": supporting_comments,
            "processed_at": str(timezone.now())
        },
        "location_summary": {
            "safety_score": safety_score,
            "recent_risky_count": 1 if severity > 0.5 else 0,
            "trend": trend
        }
    }
    
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['POST'])
def ingest_post(request):
    """
    Manual pipeline ingest
    POST /api/ingest
    Body: {"source": "manual", "source_id": "123", "text": "...", "created_at": "..."}
    """
    serializer = PostSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        
        # TRIGGER BACKGROUND NLP TASK HERE to classify and geocode this new Post mathematically
        async_task('api.tasks.process_post_nlp', serializer.instance.id)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .models import UserURL
from .serializers import UserURLSerializer

@api_view(['GET', 'POST'])
def manage_user_urls(request):
    """
    GET: List active URLs submitted by the user.
    POST: Add a new URL to be monitored by the 3-hour cron.
    """
    if request.method == 'GET':
        urls = UserURL.objects.filter(is_active=True).order_by('-added_at')
        serializer = UserURLSerializer(urls, many=True)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        url = request.data.get('url')
        if not url:
            return Response({"error": "URL is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        instance, created = UserURL.objects.get_or_create(url=url)
        if not created and not instance.is_active:
            instance.is_active = True
            instance.save()
            
        serializer = UserURLSerializer(instance)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)
