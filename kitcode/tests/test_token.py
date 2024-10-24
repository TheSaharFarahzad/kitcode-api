import jwt
from datetime import timedelta

import pytest

from django.conf import settings
from users.models import User
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APITestCase


class TestJWTAuthentication(APITestCase):
    PASSWORD = "testpassword"

    def setUp(self):
        self.user = User.objects.create_user(
            username="normal_user", email="normal_user@test.com"
        )
        self.user.set_password(self.PASSWORD)
        self.user.save()

        self.super_user = User.objects.create_user(
            username="super_user", email="super_user@test.com"
        )
        self.super_user.set_password(self.PASSWORD)
        self.super_user.is_superuser = True
        self.super_user.save()

        self.expired_token = jwt.encode(
            {
                "user_id": self.user.id,
                "exp": timezone.now() - timedelta(seconds=1),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        self.obtain_token_url = reverse("token_obtain_pair")
        self.refresh_token_url = reverse("token_refresh")

    def test_obtain_token_with_normal_user(self):
        data = {
            "username": "normal_user",
            "password": self.PASSWORD,
        }
        response = self.client.post(self.obtain_token_url, data=data)
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

        self.access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

    def test_obtain_token_with_super_user(self):
        data = {
            "username": "super_user",
            "password": self.PASSWORD,
        }
        response = self.client.post(self.obtain_token_url, data=data)
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

        self.access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

    def test_obtain_token_with_not_created_user(self):
        data = {
            "username": "non_existing_user",
            "password": self.PASSWORD,
        }
        response = self.client.post(self.obtain_token_url, data=data)
        assert response.status_code == 401
        assert "access" not in response.data
        assert "refresh" not in response.data

    def test_obtain_token_error_message_for_invalid_credentials(self):
        data = {
            "username": "normal_user",
            "password": "wrongpassword",
        }
        response = self.client.post(self.obtain_token_url, data=data)
        assert response.status_code == 401
        assert (
            response.data["detail"]
            == "No active account found with the given credentials"
        )

    @pytest.mark.skip(reason="After adding Django Rest Framework throttling")
    def test_limit_token_requests(self):
        for _ in range(5):
            data = {
                "username": "normal_user",
                "password": self.PASSWORD,
            }
            response = self.client.post(self.obtain_token_url, data=data)
            assert response.status_code == 200

        response = self.client.post(self.obtain_token_url, data=data)
        assert response.status_code == 429

    def test_refresh_token_with_valid_token(self):
        # First obtain a token
        data = {
            "username": "normal_user",
            "password": self.PASSWORD,
        }
        response = self.client.post(self.obtain_token_url, data=data)
        self.refresh_token = response.data["refresh"]

        # Now test refreshing the token
        refresh_data = {
            "refresh": self.refresh_token,
        }
        refresh_response = self.client.post(self.refresh_token_url, data=refresh_data)
        assert refresh_response.status_code == 200
        assert "access" in refresh_response.data

    def test_refresh_token_with_invalid_token(self):
        data = {
            "refresh": "invalid_refresh_token",
        }
        response = self.client.post(self.refresh_token_url, data=data)
        assert response.status_code == 401

    def test_refresh_token_with_expired_token(self):
        refresh_data = {
            "refresh": self.expired_token,
        }
        response = self.client.post(self.refresh_token_url, data=refresh_data)
        assert response.status_code == 401
        assert "access" not in response.data

    def test_refresh_token_creates_new_access_token(self):
        data = {
            "username": "normal_user",
            "password": self.PASSWORD,
        }
        response = self.client.post(self.obtain_token_url, data=data)
        original_access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

        # Use the refresh token to request a new access token
        refresh_data = {
            "refresh": self.refresh_token,
        }
        refresh_response = self.client.post(self.refresh_token_url, data=refresh_data)
        new_access_token = refresh_response.data["access"]

        # Verify that the new access token is different from the original one
        assert original_access_token != new_access_token
