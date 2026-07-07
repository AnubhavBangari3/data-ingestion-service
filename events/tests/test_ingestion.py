import json

import pytest
from rest_framework.test import APIClient

from events.models import Event


pytestmark = pytest.mark.django_db


def valid_event():
    return {
        "event_id": "evt_1001",
        "tenant_id": "tenant_1",
        "source": "web",
        "event_type": "click",
        "timestamp": "2026-07-07T12:30:00Z",
        "payload": {
            "page": "home"
        },
    }


def test_single_event_ingestion():
    client = APIClient()

    response = client.post(
        "/api/events/",
        data=valid_event(),
        format="json",
    )

    assert response.status_code == 201
    assert Event.objects.count() == 1

    event = Event.objects.first()

    assert event.event_id == "evt_1001"
    assert event.tenant_id == "tenant_1"
    assert event.source == "web"
    assert event.event_type == "click"


def test_duplicate_event_is_idempotent():
    client = APIClient()

    payload = valid_event()

    first = client.post(
        "/api/events/",
        data=payload,
        format="json",
    )

    second = client.post(
        "/api/events/",
        data=payload,
        format="json",
    )

    assert first.status_code == 201
    assert second.status_code == 200

    assert Event.objects.count() == 1


def test_missing_required_field():
    client = APIClient()

    payload = valid_event()
    payload.pop("tenant_id")

    response = client.post(
        "/api/events/",
        data=payload,
        format="json",
    )

    assert response.status_code == 400
    assert Event.objects.count() == 0


def test_reject_naive_timestamp():
    client = APIClient()

    payload = valid_event()
    payload["timestamp"] = "2026-07-07T12:30:00"

    response = client.post(
        "/api/events/",
        data=payload,
        format="json",
    )

    assert response.status_code == 400
    assert "timestamp" in response.data


def test_reject_large_payload():
    client = APIClient()

    payload = valid_event()

    payload["payload"] = {
        "data": "A" * (70 * 1024)
    }

    response = client.post(
        "/api/events/",
        data=payload,
        format="json",
    )

    assert response.status_code == 400
    assert "payload" in response.data