from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings


class APIVersionView(APIView):

    def get(self, request):
        # Get the version from query parameters, defaulting to the configured default version
        version = request.query_params.get(
            "version", settings.REST_FRAMEWORK["DEFAULT_VERSION"]
        )

        # If no version is provided in the query parameters, use the default version
        if not version:
            version = settings.REST_FRAMEWORK["DEFAULT_VERSION"]

        # Check if the version is valid; return a 404 if not
        if version not in settings.REST_FRAMEWORK["VALID_VERSIONS"]:
            return Response(
                {"error": "Invalid version."}, status=status.HTTP_404_NOT_FOUND
            )

        # Return the requested version
        return Response({"version": version}, status=status.HTTP_200_OK)
