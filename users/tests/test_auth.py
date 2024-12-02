# Standard library imports
from unittest.mock import patch

# Django imports
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from allauth.account.models import EmailAddress

# Third-party imports
from rest_framework import status
from rest_framework.test import APIClient
import pytest


User = get_user_model()


@pytest.fixture
def api_client():
    """Provides an instance of APIClient."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Fixture to create a new user."""

    def _create_user(email, password, username, is_active=True):
        User = get_user_model()
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.is_active = is_active
        user.save()
        return user

    return _create_user


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


def _mark_email_verified(user):
    """Helper function to mark the user's email as verified."""
    EmailAddress.objects.create(
        user=user, email=user.email, verified=True, primary=True
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "register_data, expected_status, expected_error_field, expected_error_message",
    [
        # Test missing email
        (
            {
                "username": "missingemail",
                "email": "",
                "password1": "password123",
                "password2": "password123",
                "first_name": "",
                "last_name": "",
            },
            status.HTTP_400_BAD_REQUEST,
            ["email"],
            "This field may not be blank.",
        ),
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
    create_user("existing_username@example.com", "Sfrc.123", "existing_username")

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
    ACCOUNT_EMAIL_CONFIRMATION_HMAC=False,
)
@pytest.mark.parametrize(
    "register_data, expected_status, expected_error_field, expected_error_message",
    [
        # Test email already registered
        (
            {
                "username": "existing",
                "email": "existing_email@example.com",
                "password1": "Sfrc.123",
                "password2": "Sfrc.123",
                "first_name": "Existing",
                "last_name": "User",
            },
            status.HTTP_400_BAD_REQUEST,
            ["email"],
            "A user is already registered with this e-mail address.",
        ),
    ],
)
def test_register_user_if_email_already_registered(
    api_client,
    register_data,
    expected_status,
    expected_error_field,
    expected_error_message,
):
    # Create the user before running the test
    data = {
        "username": "existing_email",
        "email": "existing_email@example.com",
        "password1": "Sfrc.123",
        "password2": "Sfrc.123",
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
    key = email_confirmation.key
    # Verify the email
    verify_url = reverse("rest_verify_email")
    response = api_client.post(verify_url, data={"key": key})
    # Assert the expected status
    assert response.status_code == status.HTTP_200_OK

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
        (
            "nonexistent@example.com",
            status.HTTP_400_BAD_REQUEST,
            "Email address not found.",
        ),
        (
            "",
            status.HTTP_400_BAD_REQUEST,
            "This field may not be blank.",
        ),
    ],
)
def test_resend_email_verification(
    api_client,
    email,
    expected_status,
    expected_error,
):
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


@pytest.mark.django_db
@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="mandatory",
    ACCOUNT_EMAIL_REQUIRED=True,
    ACCOUNT_EMAIL_CONFIRMATION_HMAC=False,
)
def test_registration_user_creation(api_client):
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
        # Valid login without username
        (
            {
                "email": "newuser@example.com",
                "password": "Sfrc.123",
            },
            status.HTTP_200_OK,
            None,
            None,
        ),
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
        # Invalid email
        (
            {
                "email": "invalid@example.com",
                "password": "password123",
            },
            status.HTTP_400_BAD_REQUEST,
            "non_field_errors",
            "Unable to log in with provided credentials.",
        ),
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
    user = create_user(
        username="newuser", email="newuser@example.com", password="Sfrc.123"
    )

    # Mark the user's email as verified to avoid email verification issues
    _mark_email_verified(user)

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


@pytest.mark.django_db
@override_settings(ACCOUNT_LOGOUT_ON_GET=True)
@pytest.mark.parametrize(
    "auth_header, expected_status, expected_detail",
    [
        (  # Valid authentication
            "Bearer {token}",
            status.HTTP_200_OK,
            "Successfully logged out.",
        ),
        (  # No authentication provided
            None,
            status.HTTP_400_BAD_REQUEST,
            "You should be logged in to logout. Check whether the token is passed.",
        ),
        (  # Invalid token
            "Bearer invalidtoken123",
            status.HTTP_401_UNAUTHORIZED,
            "Given token not valid for any token type",
        ),
    ],
)
def test_logout(
    api_client,
    create_user,
    auth_header,
    expected_status,
    expected_detail,
):
    # Step 1: Create a user and obtain a valid token
    user = create_user(
        username="newuser", email="newuser@example.com", password="Sfrc.123"
    )
    obtain_token_url = reverse("token_obtain_pair")
    login_data = {"username": "newuser", "password": "Sfrc.123"}
    response = api_client.post(obtain_token_url, data=login_data)

    assert response.status_code == status.HTTP_200_OK
    token = response.data["access"]

    # Step 2: Set the appropriate authorization header for the test case
    if auth_header:
        if "{token}" in auth_header:
            auth_header = auth_header.format(token=token)
        api_client.credentials(HTTP_AUTHORIZATION=auth_header)

    # Step 3: Send the logout request
    rest_logout_url = reverse("rest_logout")
    logout_response = api_client.get(rest_logout_url)

    # Step 4: Assert the response status code and detail message
    assert logout_response.status_code == expected_status
    assert logout_response.data.get("detail") == expected_detail


@pytest.mark.django_db
@override_settings(ACCOUNT_LOGOUT_ON_GET=False)
@pytest.mark.parametrize(
    "auth_header, request_method, expected_status, expected_detail",
    [
        (  # Valid POST logout
            "Bearer {token}",
            "post",
            status.HTTP_200_OK,
            "Successfully logged out.",
        ),
        (  # GET logout (not allowed)
            "Bearer {token}",
            "get",
            status.HTTP_405_METHOD_NOT_ALLOWED,
            None,
        ),
        (  # POST logout without token
            None,
            "post",
            status.HTTP_400_BAD_REQUEST,
            "You should be logged in to logout. Check whether the token is passed.",
        ),
        (  # GET logout without token
            None,
            "get",
            status.HTTP_405_METHOD_NOT_ALLOWED,
            'Method "GET" not allowed.',
        ),
        (  # POST logout with invalid token
            "Bearer invalidtoken123",
            "post",
            status.HTTP_401_UNAUTHORIZED,
            "Given token not valid for any token type",
        ),
        (  # GET logout with invalid token
            "Bearer invalidtoken123",
            "get",
            status.HTTP_401_UNAUTHORIZED,
            "Given token not valid for any token type",
        ),
    ],
)
def test_logout(
    api_client,
    create_user,
    auth_header,
    request_method,
    expected_status,
    expected_detail,
):
    # Step 1: Create a user and obtain a valid token for test cases that require it
    user = create_user(
        username="newuser", email="newuser@example.com", password="Sfrc.123"
    )
    obtain_token_url = reverse("token_obtain_pair")
    payload = {"username": "newuser", "password": "Sfrc.123"}
    token_response = api_client.post(obtain_token_url, data=payload)

    assert token_response.status_code == status.HTTP_200_OK
    valid_token = token_response.data["access"]

    # Step 2: Set the authorization header if needed
    if auth_header:
        if "{token}" in auth_header:
            auth_header = auth_header.format(token=valid_token)
        api_client.credentials(HTTP_AUTHORIZATION=auth_header)

    # Step 3: Perform the request
    logout_url = reverse("rest_logout")
    if request_method == "post":
        response = api_client.post(logout_url)
    elif request_method == "get":
        response = api_client.get(logout_url)

    # Step 4: Assert the response status code and detail message
    assert response.status_code == expected_status
    if expected_detail:
        assert response.data.get("detail") == expected_detail


@pytest.mark.django_db
@pytest.mark.parametrize(
    "new_password1, new_password2, expected_status, expected_detail",
    [
        (
            "new_person",
            "new_person",
            status.HTTP_200_OK,
            "New password has been saved.",
        ),
        (
            "new_person1",
            "new_person2",
            status.HTTP_400_BAD_REQUEST,
            "The two password fields didn’t match.",
        ),
        (
            "",
            "",
            status.HTTP_400_BAD_REQUEST,
            "This field may not be blank.",
        ),
        (
            "short",
            "short",
            status.HTTP_400_BAD_REQUEST,
            "This password is too short. It must contain at least 8 characters.",
        ),
        (
            "password123",
            "password123",
            status.HTTP_400_BAD_REQUEST,
            "This password is too common.",
        ),
    ],
)
def test_change_password(
    api_client,
    create_user,
    new_password1,
    new_password2,
    expected_status,
    expected_detail,
):
    # Step 1: Create a user
    user = create_user(
        username="testuser", email="test@example.com", password="Sher.654"
    )

    # Step 2: Authenticate using force_authenticate
    api_client.force_authenticate(user=user)

    # Step 3: Attempt to change the password
    change_password_url = reverse("rest_password_change")
    password_change_payload = {
        "new_password1": new_password1,
        "new_password2": new_password2,
    }
    response = api_client.post(change_password_url, data=password_change_payload)

    # Step 4: Assert the response status and detail
    assert response.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        assert response.data.get("detail") == expected_detail
    else:
        assert expected_detail in str(response.data)


@pytest.mark.django_db
def test_change_password_unauthenticated(api_client):
    # Update the reverse name to match your application's configuration
    url = reverse("rest_password_change")
    data = {
        "old_password": "password123",
        "new_password1": "newpassword123",
        "new_password2": "newpassword123",
    }

    # Make a request without authentication
    response = api_client.post(url, data)

    # Assert that the response is unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.data


@pytest.mark.django_db
@patch("django.core.mail.EmailMessage.send")
@pytest.mark.parametrize(
    "username, email, reset_email, exists, is_active, expected_status, mock_email_called",
    [
        # Valid email, user exists, and is active - email should be sent.
        (
            "valid-email",
            "valid-email@example.com",
            "valid-email@example.com",
            True,
            True,
            200,
            True,
        ),
        # Valid email, but user does not exist - should return 400 and not send email.
        (
            "",
            "",
            "nonexistent@example.com",
            False,
            False,
            400,
            False,
        ),
        # Empty email - should return 400 and not send email.
        (
            "valid",
            "valid@example.com",
            "",
            False,
            True,
            400,
            False,
        ),
        # Valid email, user exists, but is inactive - should return 400 and not send email.
        (
            "inactive",
            "inactive@example.com",
            "inactive@example.com",
            True,
            False,
            400,
            False,
        ),
        # Invalid email format - should return 400 and not send email.
        (
            "invalid-email",
            "invalid-email@example.com",
            "invalid-email",
            False,
            True,
            400,
            False,
        ),
    ],
)
def test_password_reset(
    mock_email_send,
    api_client,
    create_user,
    username,
    email,
    reset_email,
    exists,
    is_active,
    expected_status,
    mock_email_called,
):
    # If the user should exist, create a user with the specified email and active state.
    if exists:
        create_user(
            username=username,
            email=email,
            password="password123",
            is_active=is_active,
        )

    # Make a POST request to the password reset endpoint with the provided email.
    url = reverse("rest_password_reset")
    response = api_client.post(url, {"email": reset_email})

    # Assert the response status matches the expected status.
    assert response.status_code == expected_status

    # Assert whether the email sending logic was triggered based on expectations.
    if mock_email_called:
        mock_email_send.assert_called_once()
    else:
        mock_email_send.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "uid_modifier, token_modifier, new_password1, new_password2, expected_status, expected_detail",
    [
        # Valid inputs
        (
            "valid_uid",
            "valid_token",
            "newpassword123",
            "newpassword123",
            200,
            "Password has been reset with the new password.",
        ),
        # Invalid UID
        (
            "invalid_uid",
            "valid_token",
            "newpassword123",
            "newpassword123",
            400,
            {"uid": ["Invalid value"]},
        ),
        # Invalid Token
        (
            "valid_uid",
            "invalid_token",
            "newpassword123",
            "newpassword123",
            400,
            {"token": ["Invalid value"]},
        ),
        # Mismatched Passwords
        (
            "valid_uid",
            "valid_token",
            "newpassword123",
            "differentpassword",
            400,
            {"new_password2": ["The two password fields didn’t match."]},
        ),
        # Missing UID
        (
            None,
            "valid_token",
            "newpassword123",
            "newpassword123",
            400,
            {"uid": ["This field is required."]},
        ),
        # Missing Token
        (
            "valid_uid",
            None,
            "newpassword123",
            "newpassword123",
            400,
            {"token": ["This field is required."]},
        ),
        # Missing Passwords
        (
            "valid_uid",
            "valid_token",
            None,
            None,
            400,
            {
                "new_password1": ["This field is required."],
                "new_password2": ["This field is required."],
            },
        ),
    ],
)
def test_password_reset_confirm(
    api_client,
    create_user,
    uid_modifier,
    token_modifier,
    new_password1,
    new_password2,
    expected_status,
    expected_detail,
):
    # Step 1: Create a user
    user = create_user(
        username="normal_user", email="normal_user@test.com", password="oldpassword123"
    )

    # Step 2: Request password reset email
    reset_url = reverse("rest_password_reset")
    response = api_client.post(reset_url, data={"email": user.email})
    assert response.status_code == 200

    # Step 3: Extract valid UID and token
    email_body = mail.outbox[0].body
    url_segment = email_body.split("password-reset/confirm/")[1]
    valid_uid, valid_token = url_segment.split("/")[:2]

    # Step 4: Modify UID and Token based on test parameters
    uid = valid_uid if uid_modifier == "valid_uid" else uid_modifier
    token = valid_token if token_modifier == "valid_token" else token_modifier

    # Step 5: Prepare the payload
    payload = {
        "uid": uid,
        "token": token,
        "new_password1": new_password1,
        "new_password2": new_password2,
    }
    payload = {k: v for k, v in payload.items() if v is not None}  # Remove None values

    # Step 6: Confirm password reset
    confirm_url = reverse("rest_password_reset_confirm")
    response = api_client.post(confirm_url, data=payload)

    # Step 7: Assert the response
    assert response.status_code == expected_status
    if isinstance(expected_detail, dict):
        assert response.data == expected_detail
    else:
        assert response.data.get("detail") == expected_detail
