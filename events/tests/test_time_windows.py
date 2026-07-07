import pytest

from django.core.management import call_command
from rest_framework.test import APIClient

from events.models import Event


pytestmark = pytest.mark.django_db


def create_event(
    event_id,
    timestamp,
    source="web",
    event_type="click",
):
    Event.objects.create(
        event_id=event_id,
        tenant_id="tenant_1",
        source=source,
        event_type=event_type,
        timestamp=timestamp,
        payload={"page": "home"},
    )


def test_events_filter_from_time():
    create_event(
        "evt1",
        "2026-07-07T12:00:00Z",
    )

    create_event(
        "evt2",
        "2026-07-07T13:00:00Z",
    )

    client = APIClient()

    response = client.get(
        "/api/events/",
        {
            "tenant_id": "tenant_1",
            "from": "2026-07-07T12:30:00Z",
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["event_id"] == "evt2"


def test_events_filter_to_time():
    create_event(
        "evt1",
        "2026-07-07T12:00:00Z",
    )

    create_event(
        "evt2",
        "2026-07-07T13:00:00Z",
    )

    client = APIClient()

    response = client.get(
        "/api/events/",
        {
            "tenant_id": "tenant_1",
            "to": "2026-07-07T12:30:00Z",
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["event_id"] == "evt1"


def test_events_filter_between_time_window():
    create_event(
        "evt1",
        "2026-07-07T12:00:00Z",
    )

    create_event(
        "evt2",
        "2026-07-07T12:30:00Z",
    )

    create_event(
        "evt3",
        "2026-07-07T13:00:00Z",
    )

    client = APIClient()

    response = client.get(
        "/api/events/",
        {
            "tenant_id": "tenant_1",
            "from": "2026-07-07T12:15:00Z",
            "to": "2026-07-07T12:45:00Z",
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["event_id"] == "evt2"


def test_metrics_filter_time_window():
    create_event(
        "evt1",
        "2026-07-07T12:00:00Z",
    )

    create_event(
        "evt2",
        "2026-07-07T13:00:00Z",
    )

    call_command("aggregate_events")

    client = APIClient()

    response = client.get(
        "/api/metrics/",
        {
            "tenant_id": "tenant_1",
            "bucket_size": "hour",
            "from": "2026-07-07T12:30:00Z",
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1


def test_minute_and_hour_bucket_queries():
    create_event(
        "evt1",
        "2026-07-07T12:30:10Z",
    )

    create_event(
        "evt2",
        "2026-07-07T12:30:40Z",
    )

    create_event(
        "evt3",
        "2026-07-07T12:45:00Z",
    )

    call_command("aggregate_events")

    client = APIClient()

    minute = client.get(
        "/api/metrics/",
        {
            "tenant_id": "tenant_1",
            "bucket_size": "minute",
        },
    )

    hour = client.get(
        "/api/metrics/",
        {
            "tenant_id": "tenant_1",
            "bucket_size": "hour",
        },
    )

    assert minute.status_code == 200
    assert hour.status_code == 200

    # Minute aggregation should produce more buckets
    assert minute.data["count"] > hour.data["count"]


def test_event_pagination():
    for i in range(5):
        create_event(
            f"evt{i}",
            f"2026-07-07T12:0{i}:00Z",
        )

    client = APIClient()

    response = client.get(
        "/api/events/",
        {
            "tenant_id": "tenant_1",
            "page": 2,
            "page_size": 2,
        },
    )

    assert response.status_code == 200
    assert len(response.data["results"]) == 2


def test_boundary_timestamp_included():
    create_event(
        "evt_boundary",
        "2026-07-07T12:30:00Z",
    )

    client = APIClient()

    response = client.get(
        "/api/events/",
        {
            "tenant_id": "tenant_1",
            "from": "2026-07-07T12:30:00Z",
            "to": "2026-07-07T12:30:00Z",
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1