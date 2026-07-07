from django.db import IntegrityError, transaction
from .models import Event
def ingest_event(validated_data):
    """
    Creates a new event in an idempotent and concurrency-safe way.

    Returns:
        (event, created)
    """
    try:
        with transaction.atomic():
            event = Event.objects.create(**validated_data)
            return event, True
    except IntegrityError:
        # Another request already inserted this event.
        event = Event.objects.get(event_id=validated_data["event_id"])
        return event, False