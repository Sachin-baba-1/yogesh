import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Post
from api.tasks import update_location_aggregates, extract_severity_and_class, mock_ner_extract_location

links_data = [
    {
        "url": "https://www.instagram.com/p/DVBc8GLEVoQ/?igsh=MTluODRjM3RseWZqbw==",
        "text": "A small argument a life lost forever. In Hyderabad, a routine disagreement between a newly married couple over lowering the TV volume reportedly turned into a fatal act of violence. Just eight months into their marriage, a 27-year-old man lost his life after being stabbed."
    },
    {
        "url": "https://www.instagram.com/p/DVBIoR4DGug/?igsh=eno5cDY0OXFjczRi",
        "text": "A shocking incident in Bangalore has left many disturbed after a 76-year-old retired ISRO employee allegedly killed his wife inside their home. Police said the man strangled his 63-year-old wife using a towel while she was in the kitchen."
    },
    {
        "url": "https://instagram.com/reel/DRKKb1cDBmB",
        "text": "Shocking footage from Delhi shows a severe road rage incident where a group of individuals violently attacked a driver late at night, causing severe injuries and panic in the neighborhood." 
    }
]

for item in links_data:
    severity, classification = extract_severity_and_class(item['text'])
    loc_name, lat, lon = mock_ner_extract_location(item['text'])
    
    if lat and lon:
        post, _ = Post.objects.get_or_create(
            source_id=item['url'],
            defaults={
                'source': 'user_link_analyzer',
                'text': item['text'][:1000],
                'classification': classification,
                'severity': severity,
                'geo_lat': lat,
                'geo_lon': lon,
                'created_at': timezone.now(),
                'metadata_json': {'extracted_location': loc_name}
            }
        )
        update_location_aggregates(post)
        print(f"Mapped {item['url']} -> {loc_name} ({classification}, severity {severity}) @ {lat}, {lon}")
    else:
        print(f"Failed to extract location for {item['url']}")
