from rest_framework import serializers


class EventQuerySerializer(serializers.Serializer):
    tenant_id = serializers.CharField(required=True)
    source = serializers.CharField(required=False)
    event_type = serializers.CharField(required=False)
    from_time = serializers.DateTimeField(required=False)
    to_time = serializers.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        data = kwargs.get("data")

        if data is not None:
            data = data.copy()

            if "from" in data:
                data["from_time"] = data["from"]

            if "to" in data:
                data["to_time"] = data["to"]

            kwargs["data"] = data

        super().__init__(*args, **kwargs)


class MetricsQuerySerializer(serializers.Serializer):
    tenant_id = serializers.CharField(required=True)
    bucket_size = serializers.ChoiceField(
        choices=["minute", "hour"],
        required=True,
    )
    source = serializers.CharField(required=False)
    event_type = serializers.CharField(required=False)
    from_time = serializers.DateTimeField(required=False)
    to_time = serializers.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        data = kwargs.get("data")

        if data is not None:
            data = data.copy()

            if "from" in data:
                data["from_time"] = data["from"]

            if "to" in data:
                data["to_time"] = data["to"]

            kwargs["data"] = data

        super().__init__(*args, **kwargs)