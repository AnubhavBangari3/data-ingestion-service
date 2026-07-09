from celery import shared_task
from django.core.management import call_command


@shared_task
def aggregate_events_task():
    """
    Async Celery task to run event aggregation in background.
    """
    call_command("aggregate_events")
    return "Event aggregation completed"