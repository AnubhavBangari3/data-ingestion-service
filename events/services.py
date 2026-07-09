from django.db import IntegrityError, transaction
from .models import Event
def ingest_event(validated_data):
    """
    Creates a new event in an idempotent and concurrency-safe way.

    Returns:
        (event, created)
    """
    try:
        # Execute the insert inside a database transaction
        with transaction.atomic():
            # Try to create a new event
            event = Event.objects.create(**validated_data)
            return event, True
    except IntegrityError:
        # Another request already inserted this event.
        # A duplicate event_id already exists.
        # Fetch the existing event instead of failing.
        event = Event.objects.get(event_id=validated_data["event_id"])
        return event, False
    
def bulk_ingest_events(validated_events):
    """
    Bulk inserts events while ignoring duplicate event_ids.
    """
    # Convert validated dictionaries into Event model instances
    events = [
        Event(**event_data)
        for event_data in validated_events
    ]
    # Insert events in a single database transaction
    with transaction.atomic():
        created_events = Event.objects.bulk_create(
            events,
            batch_size=1000,
            ignore_conflicts=True,# Ignore rows with duplicate event_ids
        )

    return {
        "total": len(validated_events),
        "created": len(created_events),
        "duplicates": len(validated_events) - len(created_events),
    }