import pytest
from rest_framework.test import APIClient

from events.models import Event


pytestmark = pytest.mark.django_db


def make_event(index):
    return {
        "event_id": f"evt_{index}",
        "tenant_id": "tenant_1",
        "source": "web",
        "event_type": "click",
        "timestamp": "2026-07-07T12:30:00Z",
        "payload": {
            "page": "home"
        },
    }


def test_bulk_ingestion_success():
    client = APIClient()

    payload = {
        "events": [
            make_event(1),
            make_event(2),
            make_event(3),
        ]
    }

    response = client.post(
        "/api/events/bulk/",
        data=payload,
        format="json",
    )

    assert response.status_code == 201
    assert Event.objects.count() == 3


def test_bulk_duplicate_events_are_ignored():
    client = APIClient()

    payload = {
        "events": [
            make_event(1),
            make_event(2),
        ]
    }

    response1 = client.post(
        "/api/events/bulk/",
        data=payload,
        format="json",
    )

    response2 = client.post(
        "/api/events/bulk/",
        data=payload,
        format="json",
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    assert Event.objects.count() == 2


def test_bulk_empty_request():
    client = APIClient()

    payload = {
        "events": []
    }

    response = client.post(
        "/api/events/bulk/",
        data=payload,
        format="json",
    )

    assert response.status_code == 400
    assert "events" in response.data


def test_bulk_more_than_5000_events():
    client = APIClient()

    payload = {
        "events": [
            make_event(i)
            for i in range(5001)
        ]
    }

    response = client.post(
        "/api/events/bulk/",
        data=payload,
        format="json",
    )

    assert response.status_code == 400
    assert "events" in response.data


def test_bulk_invalid_event():
    client = APIClient()

    bad_event = make_event(1)
    del bad_event["tenant_id"]

    payload = {
        "events": [
            make_event(2),
            bad_event,
        ]
    }

    response = client.post(
        "/api/events/bulk/",
        data=payload,
        format="json",
    )

    assert response.status_code == 400

    # Nothing should be inserted if validation fails
    assert Event.objects.count() == 0


def test_bulk_partial_duplicates():
    client = APIClient()

    payload1 = {
        "events": [
            make_event(1),
            make_event(2),
        ]
    }

    payload2 = {
        "events": [
            make_event(2),
            make_event(3),
            make_event(4),
        ]
    }

    client.post(
        "/api/events/bulk/",
        data=payload1,
        format="json",
    )

    response = client.post(
        "/api/events/bulk/",
        data=payload2,
        format="json",
    )

    assert response.status_code == 201

    # Final unique events: 1,2,3,4
    assert Event.objects.count() == 4