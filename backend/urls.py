from django.contrib import admin
from django.urls import path
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/ingest', views.ingest_post, name='ingest'),
    path('api/location/score', views.get_location_score, name='location-score'),
    path('api/analyze-url', views.analyze_url, name='analyze-url'),
    path('api/user-url', views.manage_user_urls, name='user-urls'),
]
