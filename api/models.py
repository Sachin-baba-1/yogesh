from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    source = models.CharField(max_length=50) # e.g. 'twitter'
    source_id = models.CharField(max_length=255, unique=True)
    text = models.TextField()
    created_at = models.DateTimeField()
    processed_at = models.DateTimeField(auto_now_add=True)
    user_handle = models.CharField(max_length=255, null=True, blank=True)
    user_location = models.CharField(max_length=255, null=True, blank=True)
    geo_lat = models.FloatField(null=True, blank=True)
    geo_lon = models.FloatField(null=True, blank=True)
    
    # Classification results
    classification = models.CharField(max_length=50, null=True, blank=True) # safe, concern, harassment, threat
    severity = models.FloatField(default=0.0) # 0.0 to 1.0
    metadata_json = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"[{self.classification}] {self.text[:50]}"

class Location(models.Model):
    name = models.CharField(max_length=255)
    # Bounding box coordinates for the rough area
    min_lat = models.FloatField()
    max_lat = models.FloatField()
    min_lon = models.FloatField()
    max_lon = models.FloatField()
    
    safety_score = models.IntegerField(default=100) # 0 - 100
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (Score: {self.safety_score})"

class LocationAggregate(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='aggregates')
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    risky_count = models.IntegerField(default=0)
    avg_severity = models.FloatField(default=0.0)
    
class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    threshold = models.IntegerField(default=50) # Alert if score drops below this
    is_active = models.BooleanField(default=True)

class UserURL(models.Model):
    """
    Stores URLs explicitly submitted by the user from the React Dashboard.
    These are polled by the 3-hour scheduled crawler.
    """
    url = models.URLField(unique=True)
    added_at = models.DateTimeField(auto_now_add=True)
    last_crawled = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.url
