import threading

import pytest
from rest_framework.test import APIClient

from events.models import Event


pytestmark = pytest.mark.django_db(transaction=True)


def event_payload():
    return {
        "event_id": "evt_concurrent",
        "tenant_id": "tenant_1",
        "source": "web",
        "event_type": "click",
        "timestamp": "2026-07-07T12:30:00Z",
        "payload": {
            "page": "home"
        },
    }


def send_request(results):
    client = APIClient()

    response = client.post(
        "/api/events/",
        data=event_payload(),
        format="json",
    )

    results.append(response.status_code)


def test_concurrent_duplicate_ingestion():
    results = []

    threads = [
        threading.Thread(
            target=send_request,
            args=(results,),
        )
        for _ in range(10)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Only one row should exist
    assert Event.objects.count() == 1

    # One request inserts the row
    assert results.count(201) == 1

    # Remaining requests detect the duplicate
    assert results.count(200) == 9


def test_concurrent_multiple_unique_events():
    results = []

    def worker(index):
        client = APIClient()

        payload = {
            "event_id": f"evt_{index}",
            "tenant_id": "tenant_1",
            "source": "web",
            "event_type": "click",
            "timestamp": "2026-07-07T12:30:00Z",
            "payload": {
                "page": "home"
            },
        }

        response = client.post(
            "/api/events/",
            data=payload,
            format="json",
        )

        results.append(response.status_code)

    threads = [
        threading.Thread(
            target=worker,
            args=(i,),
        )
        for i in range(10)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert Event.objects.count() == 10

    assert results.count(201) == 10


def test_bulk_duplicate_after_concurrent_requests():
    client = APIClient()

    threads = [
        threading.Thread(
            target=send_request,
            args=([],),
        )
        for _ in range(5)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    response = client.post(
        "/api/events/bulk/",
        data={
            "events": [
                event_payload()
            ]
        },
        format="json",
    )

    assert response.status_code == 201

    # Still only one event
    assert Event.objects.count() == 1