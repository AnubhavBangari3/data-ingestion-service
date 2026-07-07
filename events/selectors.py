from .models import Event, EventAggregate


def get_events(
    tenant_id,
    source=None,
    event_type=None,
    from_time=None,
    to_time=None,
):
    queryset = Event.objects.filter(tenant_id=tenant_id)

    if source:
        queryset = queryset.filter(source=source.lower())

    if event_type:
        queryset = queryset.filter(event_type=event_type.lower())

    if from_time:
        queryset = queryset.filter(timestamp__gte=from_time)

    if to_time:
        queryset = queryset.filter(timestamp__lte=to_time)

    return queryset.order_by("timestamp", "id")


def get_metrics(
    tenant_id,
    bucket_size,
    source=None,
    event_type=None,
    from_time=None,
    to_time=None,
):
    queryset = EventAggregate.objects.filter(
        tenant_id=tenant_id,
        bucket_size=bucket_size,
    )

    if source:
        queryset = queryset.filter(source=source.lower())

    if event_type:
        queryset = queryset.filter(event_type=event_type.lower())

    if from_time:
        queryset = queryset.filter(bucket_start__gte=from_time)

    if to_time:
        queryset = queryset.filter(bucket_start__lte=to_time)

    return queryset.order_by("bucket_start", "id")