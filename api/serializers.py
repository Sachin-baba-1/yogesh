from rest_framework import serializers
from .models import Post, Location, LocationAggregate, Alert, UserURL

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

class LocationAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationAggregate
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    aggregates = LocationAggregateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Location
        fields = ['id', 'name', 'min_lat', 'max_lat', 'min_lon', 'max_lon', 'safety_score', 'last_updated', 'aggregates']

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'

class UserURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserURL
        fields = '__all__'
