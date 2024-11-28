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


# @pytest.fixture
# def create_user(django_user_model):


#     def _create_user(username, email, password):
#         return django_user_model.objects.create_user(
#             username=username, email=email, password=password
#         )

#     return _create_user


@pytest.fixture
def create_user(db):
    """Fixture to create a new user."""

    def _create_user(email, password, username="user", is_active=True):
        User = get_user_model()
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.is_active = is_active
        user.save()
        return user

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
    create_user("existing_email@example.com", "Sfrc.123", "existing_email")
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
    "old_password, new_password1, new_password2, expected_status, expected_detail",
    [
        (
            "Sher.654",
            "new_person",
            "new_person",
            status.HTTP_200_OK,
            "New password has been saved.",
        ),
        (
            "Sher.654",
            "new_person1",
            "new_person2",
            status.HTTP_400_BAD_REQUEST,
            "The two password fields didn’t match.",
        ),
        # (
        #     "wrong_password",
        #     "new_person",
        #     "new_person",
        #     status.HTTP_400_BAD_REQUEST,
        #     "Your old password was entered incorrectly.",
        # ),
        (
            "Sher.654",
            "",
            "",
            status.HTTP_400_BAD_REQUEST,
            "This field may not be blank.",
        ),
        (
            "Sher.654",
            "short",
            "short",
            status.HTTP_400_BAD_REQUEST,
            "This password is too short. It must contain at least 8 characters.",
        ),
    ],
)
def test_change_password(
    api_client,
    create_user,
    old_password,
    new_password1,
    new_password2,
    expected_status,
    expected_detail,
):
    """
    Test password change behavior under different scenarios:
    - Valid and invalid old passwords (not implemented yet)
    - Matching and non-matching new passwords
    - Valid and invalid new passwords (e.g., too short)
    """
    # Step 1: Create a user
    user = create_user(
        username="testuser", email="test@example.com", password="Sher.654"
    )

    # Step 2: Authenticate using force_authenticate
    api_client.force_authenticate(user=user)

    # Step 3: Attempt to change the password
    change_password_url = reverse("rest_password_change")
    password_change_payload = {
        "old_password": old_password,
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
    """
    Test that an unauthenticated user cannot change the password.
    """
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
    "email, exists, is_active, expected_status, mock_email_called",
    [
        # Valid email, user exists, and is active - email should be sent.
        (
            "test@example.com",
            True,
            True,
            200,
            True,
        ),
        # # Valid email, but user does not exist - should return 400 and not send email.
        # (
        #     "nonexistent@example.com",
        #     False,
        #     True,
        #     400,
        #     False,
        # ),
        # Empty email - should return 400 and not send email.
        (
            "",
            False,
            True,
            400,
            False,
        ),
        # # Valid email, user exists, but is inactive - should return 400 and not send email.
        # (
        #     "inactive@example.com",
        #     True,
        #     False,
        #     400,
        #     False,
        # ),
        # Invalid email format - should return 400 and not send email.
        (
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
    email,
    exists,
    is_active,
    expected_status,
    mock_email_called,
):
    """
    Test the password reset endpoint with various email inputs and user states.
    """
    # If the user should exist, create a user with the specified email and active state.
    if exists:
        create_user(email=email, password="password123", is_active=is_active)

    # Make a POST request to the password reset endpoint with the provided email.
    url = reverse("rest_password_reset")
    response = api_client.post(url, {"email": email})

    # Assert the response status matches the expected status.
    assert response.status_code == expected_status

    # Assert whether the email sending logic was triggered based on expectations.
    if mock_email_called:
        mock_email_send.assert_called_once()
    else:
        mock_email_send.assert_not_called()


# @pytest.mark.django_db
# @patch("accounts.email.send_email")
# def test_password_reset_email(mock_send_email, api_client, create_user):

#     user = create_user(email="test@example.com", password="oldpassword123")
#     url = reverse("password-reset")
#     response = api_client.post(url, {"email": user.email})
#     assert response.status_code == 200
#     assert "Password reset email sent." in response.data.get("message", "")

#     # Simulate valid UID and token (mocked for the test)
#     uidb64 = urlsafe_base64_encode(force_bytes(user.pk))  # Mocked UID encoding
#     token = "valid-token"  # This should be a valid token generated in your app

#     # Prepare the data for the request
#     data = {
#         "new_password": "newpassword123",
#         "confirm_password": "newpassword123",
#         "uidb64": uidb64,
#         "token": token,
#     }

#     # Call the password reset confirm view
#     url = reverse("password-reset-confirm", kwargs={"uidb64": uidb64, "token": token})
#     response = api_client.post(url, data)

#     # Assert: Check if the response is correct and send_email was called
#     assert response.status_code == 200
#     assert "Password reset successful." in response.data.get("message", response.data)


# @pytest.mark.django_db
# @pytest.mark.parametrize(
#     "new_password, confirm_password, expected_status, error_field, expected_message",
#     [
#         # Valid password reset
#         (
#             "newpassword123",
#             "newpassword123",
#             200,
#             "message",
#             "Password reset successful.",
#         ),
#         # Passwords do not match
#         (
#             "newpassword123",
#             "differentpassword123",
#             400,
#             "password",
#             "Passwords must match.",
#         ),
#         # New password is too short
#         (
#             "short",
#             "short",
#             400,
#             "new_password",
#             "Password must be at least 8 characters long.",
#         ),
#         # New password is same as old password
#         (
#             "oldpassword123",
#             "oldpassword123",
#             400,
#             "new_password",
#             "New password cannot be the same as the old one.",
#         ),
#         # Missing required fields
#         (
#             "",
#             "",
#             400,
#             "new_password",
#             "This field may not be blank.",
#         ),
#     ],
# )
# @patch("accounts.email.send_email")
# def test_password_reset_confirm(
#     mock_send_email,
#     api_client,
#     create_user,
#     new_password,
#     confirm_password,
#     expected_status,
#     error_field,
#     expected_message,
# ):
#     # Create a valid user for testing
#     user = create_user(email="test@example.com", password="oldpassword123")

#     # Simulate valid UID and token (mocked for the test)
#     uidb64 = urlsafe_base64_encode(force_bytes(user.pk))  # Mocked UID encoding
#     token = "valid-token"  # This should be a valid token generated in your app

#     # Prepare the data for the request
#     data = {
#         "new_password": new_password,
#         "confirm_password": confirm_password,
#         "uidb64": uidb64,
#         "token": token,
#     }

#     # Call the password reset confirm view
#     url = reverse("password-reset-confirm", kwargs={"uidb64": uidb64, "token": token})
#     response = api_client.post(url, data)

#     # Assert the response status code
#     assert response.status_code == expected_status

#     # For error status codes, check for error message in the specified error field
#     if expected_status == 400:
#         # Get the error details from the response
#         error_field_data = response.data.get(error_field)

#         # If the error is a dictionary (nested error structure), get the specific error message
#         if isinstance(error_field_data, dict):
#             # Check if the error is inside the nested dictionary under the same error field
#             error_field_data = error_field_data.get(error_field, "")

#         assert expected_message in str(error_field_data)
#     else:
#         # For successful responses, check the message in the response
#         assert expected_message in response.data.get(error_field, response.data)