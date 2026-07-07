from django.urls import path

from .views import (
    EventIngestionView,
    BulkEventIngestionView,
    MetricsView,
)

urlpatterns = [
    path("events/", EventIngestionView.as_view()),
    path("events/bulk/", BulkEventIngestionView.as_view()),
    path("metrics/", MetricsView.as_view()),
]