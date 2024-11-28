# 1. Standard library imports
from unittest.mock import patch

# 2. Django imports
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core import mail
from django.test import override_settings

# 3. Third-party imports
from rest_framework import status
from rest_framework.test import APIClient
import pytest


User = get_user_model()

# --- Fixtures ---


@pytest.fixture
def api_client():
    """Provides an instance of APIClient."""
    return APIClient()


@pytest.fixture
def create_user(django_user_model):
    """Fixture to create a new user."""

    def _create_user(username, email, password):
        return django_user_model.objects.create_user(
            username=username, email=email, password=password
        )

    return _create_user


# --- Helper Functions ---


def get_error_message(response_data):
    """
    Extract error messages from the response data.
    Handles field-based errors and generic "detail" errors.
    """
    if "detail" in response_data:
        return str(response_data["detail"])
    for field, errors in response_data.items():
        if isinstance(errors, list) and errors:
            return str(errors[0])
    return ""


# --- Test Registration ---


@pytest.mark.django_db
@pytest.mark.parametrize(
    "register_data, expected_status, expected_error_field, expected_error_message",
    [
        # # Test missing email
        # (
        #     {
        #         "username": "missingemail",
        #         "email": "",
        #         "password1": "password123",
        #         "password2": "password123",
        #         "first_name": "",
        #         "last_name": "",
        #     },
        #     status.HTTP_400_BAD_REQUEST,
        #     ["email"],
        #     "This field may not be blank.",
        # ),
        # Test missing password
        (
            {
                "username": "missingfields",
                "email": "missingfields@example.com",
                "password1": "",
                "password2": "",
                "first_name": "No",
                "last_name": "Password",
            },
            status.HTTP_400_BAD_REQUEST,
            ["password1", "password2"],
            "This field may not be blank.",
        ),
        # Test missing password confirmation
        (
            {
                "username": "missingpasswordconfirmation",
                "email": "missingpasswordconfirmation@example.com",
                "password1": "password123",
                "first_name": "No",
                "last_name": "Confirmation",
            },
            status.HTTP_400_BAD_REQUEST,
            ["password2"],
            "This field is required.",
        ),
        # Test invalid email format
        (
            {
                "username": "invalidemailformat",
                "email": "invalidemailformat.com",
                "password1": "password123",
                "password2": "password123",
                "first_name": "Invalid",
                "last_name": "Email",
            },
            status.HTTP_400_BAD_REQUEST,
            ["email"],
            "Enter a valid email address.",
        ),
        # # Test email already registered
        # (
        #     {
        #         "username": "existing",
        #         "email": "existing_email@example.com",
        #         "password1": "Sfrc.123",
        #         "password2": "Sfrc.123",
        #         "first_name": "Existing",
        #         "last_name": "User",
        #     },
        #     status.HTTP_400_BAD_REQUEST,
        #     ["email"],
        #     "A user with this email already exists.",
        # ),
        # Test username already registered
        (
            {
                "username": "existing_username",
                "email": "existing@example.com",
                "password1": "Sfrc.123",
                "password2": "Sfrc.123",
                "first_name": "Existing",
                "last_name": "User",
            },
            status.HTTP_400_BAD_REQUEST,
            ["username"],
            "A user with that username already exists.",
        ),
        # Test weak password (less than 8 characters)
        (
            {
                "username": "weakpassword",
                "email": "weakpassword@example.com",
                "password1": "short",
                "password2": "short",
                "first_name": "Weak",
                "last_name": "Password",
            },
            status.HTTP_400_BAD_REQUEST,
            ["password1"],
            "This password is too short. It must contain at least 8 characters.",
        ),
        # Test weak password (too common)
        (
            {
                "username": "commonpassword",
                "email": "commonpassword@example.com",
                "password1": "password123",
                "password2": "password123",
                "first_name": "Common",
                "last_name": "Password",
            },
            status.HTTP_400_BAD_REQUEST,
            ["password1"],
            "This password is too common.",
        ),
        # Test wrong password confirmation
        (
            {
                "username": "wrongconfirmation",
                "email": "wrongconfirmation@example.com",
                "password1": "Sfrc.123",
                "password2": "Sfrc.456",
                "first_name": "Wrong",
                "last_name": "Confirmation",
            },
            status.HTTP_400_BAD_REQUEST,
            ["non_field_errors"],
            "The two password fields didn't match.",
        ),
        # Test valid registration (to make sure it's valid)
        (
            {
                "username": "validuser",
                "email": "validuser@example.com",
                "password1": "Sfrc.453",
                "password2": "Sfrc.453",
                "first_name": "Valid",
                "last_name": "User",
            },
            status.HTTP_201_CREATED,
            None,
            None,
        ),
    ],
)
@patch("dj_rest_auth.registration.views.allauth_account_settings.EMAIL_VERIFICATION")
def test_register_user(
    mock_send_email,
    api_client,
    register_data,
    expected_status,
    expected_error_field,
    expected_error_message,
    create_user,
):

    # If the email is already registered, create the user before running the test
    create_user("existing_email", "existing_email@example.com", "Sfrc.123")
    create_user("existing_username", "existing_username@example.com", "Sfrc.123")

    # Run the registration process
    register_url = reverse("rest_register")
    response = api_client.post(register_url, data=register_data)

    # Assert the status code matches the expected status
    assert response.status_code == expected_status

    # If an error is expected, check for the field and the error message
    if expected_error_field:
        # Check each expected error field
        for field in expected_error_field:
            assert field in response.data  # Verify the field exists in the response
            if expected_error_message:
                # Check if the expected message is in the field's error list
                assert expected_error_message in response.data[field]


@pytest.mark.django_db
@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="mandatory",
    ACCOUNT_EMAIL_REQUIRED=True,
)
def test_user_registration_email_sent(api_client):
    """Test that a confirmation email is sent upon successful registration."""
    user_count = User.objects.count()
    mail_count = len(mail.outbox)

    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password1": "StrongPassword123",
        "password2": "StrongPassword123",
    }
    response = api_client.post(reverse("rest_register"), data=data)
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.count() == user_count + 1
    assert len(mail.outbox) == mail_count + 1


# --- Test Email Verification ---


@pytest.mark.django_db
@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="mandatory",
    ACCOUNT_EMAIL_REQUIRED=True,
    ACCOUNT_EMAIL_CONFIRMATION_HMAC=False,
)
@pytest.mark.parametrize(
    "key, expected_status, expected_error",
    [
        (
            "valid-key",
            status.HTTP_200_OK,
            None,
        ),
        (
            "invalid-key",
            status.HTTP_404_NOT_FOUND,
            "Not found.",
        ),
        (
            "",
            status.HTTP_400_BAD_REQUEST,
            "This field may not be blank.",
        ),
    ],
)
def test_email_verification(
    api_client,
    key,
    expected_status,
    expected_error,
):
    """Test the email verification process."""
    data = {
        "username": "verifyuser",
        "email": "verifyuser@example.com",
        "password1": "StrongPassword123",
        "password2": "StrongPassword123",
    }
    response = api_client.post(reverse("rest_register"), data=data)
    assert response.status_code == status.HTTP_201_CREATED

    # Fetch confirmation key
    user = User.objects.get(email=data["email"])
    email_confirmation = (
        user.emailaddress_set.get(email=data["email"])
        .emailconfirmation_set.order_by("-created")
        .first()
    )
    # Use actual valid key if key parameter is "valid-key"
    if key == "valid-key":
        key = email_confirmation.key

    # Verify the email
    verify_url = reverse("rest_verify_email")
    response = api_client.post(verify_url, data={"key": key})

    # Assert the expected status
    assert response.status_code == expected_status

    # If an error is expected, assert its presence in the response
    if expected_error:
        error_message = get_error_message(response.data)
        assert expected_error in error_message


# --- Test Resend Email Verification ---


@pytest.mark.django_db
@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="mandatory",
    ACCOUNT_EMAIL_REQUIRED=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
@pytest.mark.parametrize(
    "email,expected_status,expected_error",
    [
        (
            "resenduser@example.com",
            status.HTTP_200_OK,
            None,
        ),
        # (
        #     "nonexistent@example.com",
        #     status.HTTP_400_BAD_REQUEST,
        #     "Email address not found.",
        # ),
        # (
        #     "",
        #     status.HTTP_400_BAD_REQUEST,
        #     "This field may not be blank.",
        # ),
    ],
)
def test_resend_email_verification(
    api_client,
    email,
    expected_status,
    expected_error,
):
    """Test resending the email verification link."""
    # Register a user
    data = {
        "username": "resenduser",
        "email": "resenduser@example.com",
        "password1": "StrongPassword123",
        "password2": "StrongPassword123",
    }
    api_client.post(reverse("rest_register"), data=data)

    # Resend verification email
    resend_url = reverse("rest_resend_email")
    response = api_client.post(resend_url, data={"email": email})
    assert response.status_code == expected_status
    if expected_error:
        assert expected_error in get_error_message(response.data)
    else:
        assert len(mail.outbox) > 1


# --- Miscellaneous Tests ---


@pytest.mark.django_db
@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="mandatory",
    ACCOUNT_EMAIL_REQUIRED=True,
    ACCOUNT_EMAIL_CONFIRMATION_HMAC=False,
)
def test_registration_user_creation(api_client):
    """Test that user creation works properly."""
    user_count = User.objects.count()

    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password1": "StrongPassword123",
        "password2": "StrongPassword123",
    }
    response = api_client.post(reverse("rest_register"), data=data)
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.count() == user_count + 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_data, expected_status, expected_error_key, expected_error_msg",
    [
        # # Valid login without username
        # (
        #     {
        #         "email": "newuser@example.com",
        #         "password": "Sfrc.123",
        #     },
        #     status.HTTP_200_OK,
        #     None,
        #     None,
        # ),
        # Valid login with username
        (
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Sfrc.123",
            },
            status.HTTP_200_OK,
            None,
            None,
        ),
        # Invalid without email
        (
            {
                "username": "newuser",
                "password": "password123",
            },
            status.HTTP_400_BAD_REQUEST,
            "non_field_errors",
            "Unable to log in with provided credentials.",
        ),
        # # Invalid email
        # (
        #     {
        #         "email": "invalid@example.com",
        #         "password": "password123",
        #     },
        #     status.HTTP_400_BAD_REQUEST,
        #     "non_field_errors",
        #     "Unable to log in with provided credentials.",
        # ),
        # Invalid email format
        (
            {
                "email": "newuser",
                "password": "password123",
            },
            status.HTTP_400_BAD_REQUEST,
            "email",
            "Enter a valid email address.",
        ),
        # Invalid password
        (
            {
                "username": "newuser",
                "password": "wrongpassword",
            },
            status.HTTP_400_BAD_REQUEST,
            "non_field_errors",
            "Unable to log in with provided credentials.",
        ),
    ],
)
def test_login(
    api_client,
    create_user,
    login_data,
    expected_status,
    expected_error_key,
    expected_error_msg,
):
    # Arrange: Create a user
    create_user(username="newuser", email="newuser@example.com", password="Sfrc.123")

    # Act: Attempt login
    url = reverse("rest_login")
    response = api_client.post(url, data=login_data)

    # Assert: Check status code
    assert response.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        assert "key" in response.data
        # assert "access" in response.data
        # assert "refresh" in response.data
        # assert "user" in response.data
        # user_data = response.data["user"]
        # assert user_data["email"] == "newuser@example.com"
        # assert user_data["username"] == "newuser"

    elif expected_status == status.HTTP_400_BAD_REQUEST:
        assert expected_error_key in response.data
        assert response.data[expected_error_key][0] == expected_error_msg
