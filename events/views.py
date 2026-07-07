from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    EventSerializer,
    BulkEventSerializer,
    EventAggregateSerializer,
)

from .selectors import get_events, get_metrics


from .services import (
    ingest_event,
    bulk_ingest_events,
)
from .filters import EventQuerySerializer, MetricsQuerySerializer
from .pagination import EventPagination


class EventIngestionView(GenericAPIView):
    """
    GET  /events
    POST /events
    """

    serializer_class = EventSerializer
    pagination_class = EventPagination

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event, created = ingest_event(serializer.validated_data)

        response_serializer = self.get_serializer(event)

        if created:
            return Response(
                {
                    "message": "Event ingested successfully.",
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": "Duplicate event ignored.",
                "data": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def get(self, request):
        query = EventQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        queryset = get_events(
            tenant_id=query.validated_data["tenant_id"],
            source=query.validated_data.get("source"),
            event_type=query.validated_data.get("event_type"),
            from_time=query.validated_data.get("from_time"),
            to_time=query.validated_data.get("to_time"),
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BulkEventIngestionView(APIView):
    """
    POST /events/bulk
    """

    def post(self, request):
        serializer = BulkEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = bulk_ingest_events(
            serializer.validated_data["events"]
        )

        return Response(
            {
                "message": "Bulk ingestion completed.",
                **result,
            },
            status=status.HTTP_201_CREATED,
        )
    
class MetricsView(GenericAPIView):
    """
    GET /metrics
    """

    serializer_class = EventAggregateSerializer
    pagination_class = EventPagination

    def get(self, request):
        query = MetricsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        queryset = get_metrics(
            tenant_id=query.validated_data["tenant_id"],
            bucket_size=query.validated_data["bucket_size"],
            source=query.validated_data.get("source"),
            event_type=query.validated_data.get("event_type"),
            from_time=query.validated_data.get("from_time"),
            to_time=query.validated_data.get("to_time"),
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)