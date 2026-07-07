from rest_framework import serializers
from django.utils import timezone

from .models import Event, EventAggregate


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "event_id",
            "tenant_id",
            "source",
            "event_type",
            "timestamp",
            "payload",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_event_id(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("event_id cannot be empty.")

        return value

    def validate_tenant_id(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("tenant_id cannot be empty.")

        return value

    def validate_source(self, value):
        value = value.strip().lower()

        if not value:
            raise serializers.ValidationError("source cannot be empty.")

        return value

    def validate_event_type(self, value):
        value = value.strip().lower()

        if not value:
            raise serializers.ValidationError("event_type cannot be empty.")

        return value

    def validate_timestamp(self, value):
        if timezone.is_naive(value):
            raise serializers.ValidationError("timestamp must include timezone information.")

        return value.astimezone(timezone.UTC)

    def validate_payload(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("payload must be a JSON object.")

        return value
    
class BulkEventSerializer(serializers.Serializer):
    events = EventSerializer(many=True)

    MAX_EVENTS = 5000

    def validate_events(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one event is required."
            )

        if len(value) > self.MAX_EVENTS:
            raise serializers.ValidationError(
                f"Maximum {self.MAX_EVENTS} events are allowed per request."
            )

        return value
    
class EventAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventAggregate
        fields = [
            "tenant_id",
            "bucket_start",
            "bucket_size",
            "source",
            "event_type",
            "count",
            "first_seen",
            "last_seen",
        ]