import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from allauth.account.models import EmailAddress, EmailConfirmation
from django.utils.timezone import now


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):

    def _create_user(email, password, username, is_active=True, is_verified=True):
        User = get_user_model()
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.is_active = is_active
        user.save()

        email_address = EmailAddress.objects.create(
            user=user, email=email, verified=is_verified, primary=True
        )

        email_confirmation = EmailConfirmation.objects.create(
            email_address=email_address,
            key="dummy-key",
            sent=now(),
        )
        email_confirmation.save()

        return user

    return _create_user


# Helper functions for arranging data, sending requests, and validating responses


def authenticate_user(api_client, user):
    """
    Authenticate a user with the API client.

    Args:
        api_client: The APIClient instance.
        user: The user instance to authenticate.
    """
    api_client.force_authenticate(user=user)


def send_request(api_client, method, url_name, data=None, url_kwargs=None):
    """
    Send a request using the specified HTTP method.

    Args:
        api_client: The APIClient instance.
        method: HTTP method as a string (e.g., 'get', 'post', 'put', 'delete').
        url_name: The name of the URL to reverse.
        data: The request body (optional).
        url_kwargs: URL arguments for reversing the URL (optional).

    Returns:
        Response object from the APIClient.
    """
    url = reverse(url_name, kwargs=url_kwargs or {})
    method_func = getattr(api_client, method.lower())
    return method_func(url, data=data)


def validate_response(
    response, expected_status, expected_data=None, expected_error_message=None
):
    """
    Validate the status code, response data, and error messages.

    Args:
        response: The API response object.
        expected_status: The expected HTTP status code.
        expected_data: The expected response data (optional, used for success responses).
        expected_error_message: The expected error message (optional, used for error responses).

    Raises:
        AssertionError if validation fails.
    """

    assert (
        response.status_code == expected_status
    ), f"Expected {expected_status}, got {response.status_code}"

    if expected_data:
        for key, value in expected_data.items():
            assert (
                response.data.get(key) == value
            ), f"Expected {key}: {value}, got {response.data.get(key)}"

    if expected_error_message:
        if isinstance(expected_error_message, str):
            error_values = response.data.values()
            found = any(expected_error_message in str(val) for val in error_values)
            assert (
                found
            ), f"Expected error message '{expected_error_message}' not found in {response.data}"
        elif isinstance(expected_error_message, dict):
            for key, value in expected_error_message.items():
                assert (
                    response.data.get(key) == value
                ), f"Expected {key}: {value}, got {response.data.get(key)}"


def check_status_code(response, expected_status):
    """
    Check if the response status code matches the expected status.

    Args:
        response: The API response object.
        expected_status: The expected HTTP status code.

    Raises:
        AssertionError if the status code does not match.
    """
    assert (
        response.status_code == expected_status
    ), f"Expected status {expected_status}, but got {response.status_code}"


def check_successful_response(response, expected_data):
    """
    Validate the response data for successful responses (200 or 201).

    Args:
        response: The API response object.
        expected_data: The expected response data.

    Raises:
        AssertionError if the response data does not match the expected data.
    """
    response_data = response.json()
    if expected_data is not None:
        for key, value in expected_data.items():
            assert (
                response_data.get(key) == value
            ), f"Expected {key}: {value}, but got {response_data.get(key)}"


def check_error_message(response, expected_error_message):
    """
    Validate the error message for error responses (non-2xx).

    Args:
        response: The API response object.
        expected_error_message: The expected error message.

    Raises:
        AssertionError if the error message does not match.
    """
    response_data = response.json()
    error_message = extract_error_message(response_data)
    assert (
        expected_error_message in error_message
    ), f"Expected error message '{expected_error_message}', but got '{error_message}'"


def extract_error_message(response_data):
    """
    Extract error messages from the response data.

    Args:
        response_data: The JSON response data from the API.

    Returns:
        A string containing the error message, if present.
    """
    if not response_data:
        return ""
    if isinstance(response_data, dict):
        # Handle common Django Rest Framework error response formats
        if "detail" in response_data:
            return response_data["detail"]
        if "non_field_errors" in response_data:
            return response_data["non_field_errors"][0]
    return str(response_data)
