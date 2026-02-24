from django.core.management.base import BaseCommand
from api.models import Post
from api.tasks import process_post_nlp
from django.utils import timezone
import random
from api.models import LocationAggregate

# Verified fallback coordinates for major Indian Cities
CITY_COORDS = {
    "Hyderabad": (17.3850, 78.4867),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Delhi": (28.6139, 77.2090),
    "Kolkata": (22.5726, 88.3639),
    "Ahmedabad": (23.0225, 72.5714),
    "Gurugram": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910)
}

class Command(BaseCommand):
    help = 'Seeds the database with simulated historical threats across major Indian IT/Metro hubs to prevent an empty map on first load.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting DB Pre-seeding process with fallback coordinates...'))
        
        # We only want to seed if the database is relatively empty
        if Post.objects.count() > 25:
            self.stdout.write(self.style.SUCCESS('Database already contains > 25 posts. Skipping seed to prevent duplicate floods.'))
            return
            
        seed_data = [
            {"city": "Hyderabad", "text": "Walking near HITEC City, harassment by a group of men following me.", "severity": 0.8, "class": "threat"},
            {"city": "Hyderabad", "text": "Unsafe conditions near Jubilee Hills late at night, constant stalking.", "severity": 0.7, "class": "concern"},
            {"city": "Mumbai", "text": "Creep hanging around Andheri station, feel very danger and threat.", "severity": 0.9, "class": "threat"},
            {"city": "Mumbai", "text": "Good police patrol near Bandra today, feeling safe.", "severity": 0.1, "class": "safe"},
            {"city": "Bangalore", "text": "Unsafe auto driver near Koramangala, threat of abduction.", "severity": 0.85, "class": "threat"},
            {"city": "Bangalore", "text": "Harassment incident reported near Indiranagar pubs.", "severity": 0.6, "class": "concern"},
            {"city": "Delhi", "text": "Gundagardi and chhedkhani near Connaught Place, very unsafe.", "severity": 0.95, "class": "threat"},
            {"city": "Delhi", "text": "Attack on a woman near Hauz Khas village last night.", "severity": 0.9, "class": "threat"},
            {"city": "Kolkata", "text": "Pareshan by stalkers near Park Street, need help bachaao.", "severity": 0.8, "class": "threat"},
            {"city": "Ahmedabad", "text": "Safe and peaceful evening walk near SG Highway.", "severity": 0.05, "class": "safe"},
            {"city": "Gurugram", "text": "Unsafe dark stretch near Cyber Hub, risk of assault.", "severity": 0.75, "class": "concern"},
            {"city": "Noida", "text": "Hamla attempt near Sector 18 market, very high threat level.", "severity": 0.95, "class": "threat"}
        ]
        
        for idx, item in enumerate(seed_data):
            city = item['city']
            lat, lon = CITY_COORDS[city]
            
            # Add slight jitter so points in the same city don't perfectly overlap
            lat += random.uniform(-0.02, 0.02)
            lon += random.uniform(-0.02, 0.02)
            
            post = Post.objects.create(
                source='historical_seed',
                source_id=f"seed_{city}_{idx}",
                text=item['text'],
                classification=item['class'],
                severity=item['severity'],
                geo_lat=lat,
                geo_lon=lon,
                created_at=timezone.now(),
                metadata_json={'extracted_location': city}
            )
            
            # Manually trigger the Location Aggregate update (bypassing async failures)
            from api.tasks import update_location_aggregates
            update_location_aggregates(post)
            
            self.stdout.write(self.style.SUCCESS(f"Force-seeded Threat Intel for: {city} at {lat}, {lon}"))
            
        self.stdout.write(self.style.SUCCESS('Database Successfully Pre-seeded with Guaranteed Regional Threats!'))
