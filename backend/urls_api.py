from django.urls import path
from . import views

urlpatterns = [
    path('ingest', views.ingest_post, name='ingest'),
    path('location/score', views.get_location_score, name='location-score'),
    path('analyze-url', views.analyze_url, name='analyze-url'),
]
