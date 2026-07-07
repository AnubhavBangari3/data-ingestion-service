from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import EventSerializer
from .services import ingest_event


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