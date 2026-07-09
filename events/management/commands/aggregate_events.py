from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Max, Min, F
from django.db.models.functions import TruncHour, TruncMinute
from django.utils import timezone

from events.models import AggregationCheckpoint, Event, EventAggregate


class Command(BaseCommand):
    help = "Aggregate events incrementally into minute and hour buckets."

    def handle(self, *args, **options):
        self.aggregate(EventAggregate.BUCKET_MINUTE)
        self.aggregate(EventAggregate.BUCKET_HOUR)

        self.stdout.write(
            self.style.SUCCESS("Event aggregation completed.")
        )

    def aggregate(self, bucket_size):
        processing_until = timezone.now()# Process events only up to the current time
        # Execute aggregation as a single transaction
        with transaction.atomic():
            # Lock checkpoint row to prevent concurrent aggregation
            checkpoint, _ = (
                AggregationCheckpoint.objects
                .select_for_update()
                .get_or_create(
                    bucket_size=bucket_size,
                    defaults={
                        "last_processed_until": timezone.datetime.min.replace(
                            tzinfo=timezone.UTC
                        )
                    },
                )
            )
            # Fetch only events that have not been processed yet
            queryset = Event.objects.filter(
                timestamp__gt=checkpoint.last_processed_until,
                timestamp__lte=processing_until,
            )
            # Group events into minute or hour bucket
            if bucket_size == EventAggregate.BUCKET_MINUTE:
                queryset = queryset.annotate(
                    bucket_start=TruncMinute("timestamp")
                )
            else:
                queryset = queryset.annotate(
                    bucket_start=TruncHour("timestamp")
                )
            # Aggregate events by tenant, bucket, source and event type
            grouped_rows = (
                queryset
                .values(
                    "tenant_id",
                    "bucket_start",
                    "source",
                    "event_type",
                )
                .annotate(
                    count=Count("id"),
                    first_seen=Min("timestamp"),
                    last_seen=Max("timestamp"),
                )
                .order_by()
            )

            for row in grouped_rows:
                # Create a new aggregate if one doesn't exist

                aggregate, created = EventAggregate.objects.get_or_create(
                    tenant_id=row["tenant_id"],
                    bucket_start=row["bucket_start"],
                    bucket_size=bucket_size,
                    source=row["source"],
                    event_type=row["event_type"],
                    defaults={
                        "count": row["count"],
                        "first_seen": row["first_seen"],
                        "last_seen": row["last_seen"],
                    },
                )

                # Update existing aggregate if already present
                if not created:
                    aggregate.count = F("count") + row["count"]
                    aggregate.first_seen = min(
                        aggregate.first_seen,
                        row["first_seen"],
                    )
                    aggregate.last_seen = max(
                        aggregate.last_seen,
                        row["last_seen"],
                    )
                    aggregate.save(update_fields=[
                        "count",
                        "first_seen",
                        "last_seen",
                        "updated_at",
                    ])

            checkpoint.last_processed_until = processing_until
            checkpoint.save(update_fields=[
                "last_processed_until",
                "updated_at",
            ])