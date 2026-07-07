from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import EventSerializer, BulkEventSerializer
from .services import ingest_event, bulk_ingest_events


class EventIngestionView(APIView):
    """
    POST /events
    """
    def post(self, request):
        serializer = EventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event, created = ingest_event(serializer.validated_data)
        response_serializer = EventSerializer(event)
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