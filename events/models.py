from django.db import models


class Event(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    tenant_id = models.CharField(max_length=255)
    source = models.CharField(max_length=100)
    event_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp", "id"]
        indexes = [
            models.Index(fields=["tenant_id", "timestamp", "id"]),
            models.Index(fields=["tenant_id", "source", "timestamp"]),
            models.Index(fields=["tenant_id", "event_type", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.event_id} - {self.tenant_id}"
    
class EventAggregate(models.Model):
    BUCKET_MINUTE = "minute"
    BUCKET_HOUR = "hour"

    BUCKET_SIZE_CHOICES = [
        (BUCKET_MINUTE, "Minute"),
        (BUCKET_HOUR, "Hour"),
    ]

    tenant_id = models.CharField(max_length=255)
    bucket_start = models.DateTimeField()
    bucket_size = models.CharField(max_length=10, choices=BUCKET_SIZE_CHOICES)

    source = models.CharField(max_length=100, null=True, blank=True)
    event_type = models.CharField(max_length=100, null=True, blank=True)

    count = models.PositiveIntegerField(default=0)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["bucket_start", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "tenant_id",
                    "bucket_start",
                    "bucket_size",
                    "source",
                    "event_type",
                ],
                name="unique_event_aggregate_bucket",
            )
        ]
        indexes = [
            models.Index(fields=["tenant_id", "bucket_size", "bucket_start"]),
            models.Index(fields=["tenant_id", "bucket_size", "source", "bucket_start"]),
            models.Index(fields=["tenant_id", "bucket_size", "event_type", "bucket_start"]),
        ]

    def __str__(self):
        return (
            f"{self.tenant_id} | {self.bucket_size} | "
            f"{self.bucket_start} | {self.count}"
        )