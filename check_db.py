import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Location, Post

print(f"Total Posts: {Post.objects.count()}")
print(f"Total Locations (Aggregates): {Location.objects.count()}")

for loc in Location.objects.all():
    print(f"Name: {loc.name}, Score: {loc.safety_score}, Bounds: {loc.min_lat}, {loc.min_lon}")
