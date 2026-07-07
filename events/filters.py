from rest_framework import serializers


class EventQuerySerializer(serializers.Serializer):
    tenant_id = serializers.CharField(required=True)
    source = serializers.CharField(required=False)
    event_type = serializers.CharField(required=False)
    from_time = serializers.DateTimeField(
        required=False,
        source="from",
    )
    to_time = serializers.DateTimeField(
        required=False,
        source="to",
    )

class MetricsQuerySerializer(serializers.Serializer):
    tenant_id = serializers.CharField(required=True)
    bucket_size = serializers.ChoiceField(
        choices=["minute", "hour"],
        required=True,
    )
    source = serializers.CharField(required=False)
    event_type = serializers.CharField(required=False)
    from_time = serializers.DateTimeField(
        required=False,
        source="from",
    )
    to_time = serializers.DateTimeField(
        required=False,
        source="to",
    )