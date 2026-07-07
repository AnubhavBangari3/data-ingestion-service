from django.db import connections
from django.db.utils import OperationalError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "healthy"})


class ReadyView(APIView):
    def get(self, request):
        try:
            connections["default"].cursor()

            return Response(
                {
                    "status": "ready",
                    "database": "ok",
                }
            )

        except OperationalError:
            return Response(
                {
                    "status": "not_ready",
                    "database": "error",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )