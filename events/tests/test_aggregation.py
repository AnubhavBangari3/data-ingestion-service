import pytest

from django.core.management import call_command
from rest_framework.test import APIClient

from events.models import Event, EventAggregate


pytestmark = pytest.mark.django_db


def create_event(
    event_id,
    tenant_id,
    source,
    event_type,
    timestamp,
):
    Event.objects.create(
        event_id=event_id,
        tenant_id=tenant_id,
        source=source,
        event_type=event_type,
        timestamp=timestamp,
        payload={"page": "home"},
    )


def test_aggregation_command_creates_minute_and_hour_buckets():
    create_event(
        "evt1",
        "tenant_1",
        "web",
        "click",
        "2026-07-07T12:30:00Z",
    )

    create_event(
        "evt2",
        "tenant_1",
        "web",
        "click",
        "2026-07-07T12:30:20Z",
    )

    create_event(
        "evt3",
        "tenant_1",
        "mobile",
        "view",
        "2026-07-07T12:31:00Z",
    )

    call_command("aggregate_events")

    minute_rows = EventAggregate.objects.filter(
        bucket_size="minute"
    )

    hour_rows = EventAggregate.objects.filter(
        bucket_size="hour"
    )

    assert minute_rows.count() == 2
    assert hour_rows.count() == 2


def test_metrics_api_returns_results():
    create_event(
        "evt1",
        "tenant_1",
        "web",
        "click",
        "2026-07-07T12:30:00Z",
    )

    create_event(
        "evt2",
        "tenant_1",
        "web",
        "click",
        "2026-07-07T12:30:30Z",
    )

    call_command("aggregate_events")

    client = APIClient()

    response = client.get(
        "/api/metrics/",
        {
            "tenant_id": "tenant_1",
            "bucket_size": "minute",
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1

    result = response.data["results"][0]

    assert result["tenant_id"] == "tenant_1"
    assert result["count"] == 2
    assert result["bucket_size"] == "minute"


def test_metrics_filter_by_source():
    create_event(
        "evt1",
        "tenant_1",
        "web",
        "click",
        "2026-07-07T12:30:00Z",
    )

    create_event(
        "evt2",
        "tenant_1",
        "mobile",
        "view",
        "2026-07-07T12:30:30Z",
    )

    call_command("aggregate_events")

    client = APIClient()

    response = client.get(
        "/api/metrics/",
        {
            "tenant_id": "tenant_1",
            "bucket_size": "minute",
            "source": "web",
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1

    assert response.data["results"][0]["source"] == "web"


def test_metrics_filter_by_event_type():
    create_event(
        "evt1",
        "tenant_1",
        "web",
        "click",
        "2026-07-07T12:30:00Z",
    )

    create_event(
        "evt2",
        "tenant_1",
        "web",
        "view",
        "2026-07-07T12:30:20Z",
    )

    call_command("aggregate_events")

    client = APIClient()

    response = client.get(
        "/api/metrics/",
        {
            "tenant_id": "tenant_1",
            "bucket_size": "minute",
            "event_type": "click",
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1


def test_aggregation_is_idempotent():
    create_event(
        "evt1",
        "tenant_1",
        "web",
        "click",
        "2026-07-07T12:30:00Z",
    )

    call_command("aggregate_events")

    first = EventAggregate.objects.count()

    call_command("aggregate_events")

    second = EventAggregate.objects.count()

    assert first == second