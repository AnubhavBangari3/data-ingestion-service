from django.urls import path

from .views import EventIngestionView

urlpatterns = [
    path("events", EventIngestionView.as_view(), name="event-ingestion"),
]