from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class APIVersionViewTests(APITestCase):

    def setUp(self):
        self.api_version_url = reverse("api-version")

    def test_api_version_url_resolves_correctly(self):
        """Test that the API version URL resolves correctly."""
        self.assertEqual(self.api_version_url, "/api/version/")

    def test_default_version_returned_when_no_version_query_param(self):
        """Test that the endpoint returns the default version when no version query parameter is provided."""
        response = self.client.get(self.api_version_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"version": "v1"})

    def test_supported_version_returned(self):
        """Test that the API version endpoint returns the supported version."""
        response = self.client.get(f"{self.api_version_url}?version=v2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"version": "v2"})

    def test_default_version_returned_with_empty_version_param(self):
        """Test that the endpoint returns the default version when the version parameter is empty."""
        response = self.client.get(f"{self.api_version_url}?version=")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"version": "v1"})

    def test_invalid_version_returns_404(self):
        """Test that the endpoint returns a 404 status for an invalid version."""
        response = self.client.get(f"{self.api_version_url}?version=v100")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Invalid version."})
