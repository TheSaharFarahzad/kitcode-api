# Standard library imports
from datetime import timedelta

# Third-party imports
import jwt
import pytest
from rest_framework import status
from rest_framework.test import APIClient

# Django imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone


User = get_user_model()


@pytest.fixture
def api_client():
    """Provides an instance of APIClient."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Fixture to create a new user."""

    def _create_user(email, password, username, is_superuser=False, is_active=True):
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.is_active = is_active
        user.is_superuser = is_superuser
        user.save()
        return user

    return _create_user


@pytest.fixture
def obtain_token_url():
    return reverse("token_obtain_pair")


@pytest.fixture
def refresh_token_url():
    return reverse("token_refresh")


@pytest.fixture
def create_tokens(api_client, create_user):
    """
    Helper fixture to create tokens for a given user.
    """

    def _create_tokens(username, password):
        data = {"username": username, "password": password}
        response = api_client.post(reverse("token_obtain_pair"), data=data)
        return response

    return _create_tokens


@pytest.mark.django_db
@pytest.mark.parametrize(
    "username,password,expected_status,expected_keys",
    [
        # Valid user
        ("normal_user", "testpassword", status.HTTP_200_OK, {"access", "refresh"}),
        # Valid superuser
        ("super_user", "testpassword", status.HTTP_200_OK, {"access", "refresh"}),
        # Non-existing user
        ("non_existing_user", "testpassword", status.HTTP_401_UNAUTHORIZED, set()),
        # Invalid credentials
        ("normal_user", "wrongpassword", status.HTTP_401_UNAUTHORIZED, set()),
    ],
)
def test_obtain_token(
    api_client,
    create_user,
    username,
    password,
    expected_status,
    expected_keys,
):
    create_user(
        email="normal_user@test.com", username="normal_user", password="testpassword"
    )
    create_user(
        email="super_user@test.com",
        username="super_user",
        password="testpassword",
        is_superuser=True,
    )

    url = reverse("token_obtain_pair")
    data = {"username": username, "password": password}

    response = api_client.post(url, data=data)

    assert response.status_code == expected_status
    assert set(response.data.keys()) >= expected_keys


@pytest.mark.django_db
@pytest.mark.parametrize(
    "refresh_token,expected_status,expected_keys",
    [
        # Valid refresh token
        ("valid_refresh_token", status.HTTP_200_OK, {"access"}),
        # Invalid refresh token
        ("invalid_refresh_token", status.HTTP_401_UNAUTHORIZED, set()),
        # Expired refresh token
        ("expired_refresh_token", status.HTTP_401_UNAUTHORIZED, set()),
    ],
)
def test_refresh_token(
    api_client,
    create_user,
    refresh_token,
    expected_status,
    expected_keys,
    obtain_token_url,
    refresh_token_url,
):
    user = create_user(
        email="user@test.com", username="testuser", password="testpassword"
    )

    # Setup valid or expired refresh token
    if refresh_token == "valid_refresh_token":
        token_response = api_client.post(
            obtain_token_url, data={"username": "testuser", "password": "testpassword"}
        )
        refresh_token = token_response.data["refresh"]

    elif refresh_token == "expired_refresh_token":
        refresh_token = jwt.encode(
            {
                "user_id": user.id,
                "exp": timezone.now() - timedelta(seconds=1),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

    data = {"refresh": refresh_token}
    response = api_client.post(refresh_token_url, data=data)

    assert response.status_code == expected_status
    assert set(response.data.keys()) >= expected_keys


@pytest.mark.django_db
def test_refresh_token_creates_new_access_token(
    api_client,
    create_user,
    create_tokens,
):
    # Create the test user
    create_user(email="user@test.com", username="testuser", password="testpassword")

    # Generate tokens
    response = create_tokens("testuser", "testpassword")

    # Debug response data
    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Token obtain failed: {response.data}"
    assert (
        "access" in response.data
    ), f"Access token missing in response: {response.data}"
    assert (
        "refresh" in response.data
    ), f"Refresh token missing in response: {response.data}"

    original_access_token = response.data["access"]
    refresh_token = response.data["refresh"]

    # Refresh token
    url = reverse("token_refresh")
    refresh_response = api_client.post(url, data={"refresh": refresh_token})

    # Debug refresh response
    assert (
        refresh_response.status_code == status.HTTP_200_OK
    ), f"Token refresh failed: {refresh_response.data}"
    assert (
        "access" in refresh_response.data
    ), f"New access token missing in refresh response: {refresh_response.data}"

    new_access_token = refresh_response.data["access"]

    # Validate the new access token
    assert original_access_token != new_access_token


@pytest.mark.django_db
@pytest.mark.skip(reason="Throttling not implemented yet")
def test_limit_token_requests(api_client, create_user, obtain_token_url):
    """
    Test that too many token requests are throttled.
    """
    create_user(email="user@test.com", username="testuser", password="testpassword")

    for _ in range(5):
        response = api_client.post(
            obtain_token_url, data={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == status.HTTP_200_OK

    # Exceed the throttle limit
    response = api_client.post(
        obtain_token_url, data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
