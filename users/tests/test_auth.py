from unittest.mock import patch
import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from .conftest import send_request, validate_response


User = get_user_model()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "register_data, expected_status, expected_data, expected_error_message",
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
            None,
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
            None,
            "This field may not be blank.",
        ),
        # Test missing password confirmation
        (
            {
                "username": "missingpasswordconfirmation",
                "email": "missingpasswordconfirmation@example.com",
                "password1": "Sfrc.453",
                "first_name": "No",
                "last_name": "Confirmation",
            },
            status.HTTP_400_BAD_REQUEST,
            None,
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
            None,
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
            None,
            "A user with that username already exists.",
        ),
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
            None,
            "A user is already registered with this e-mail address.",
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
            None,
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
            None,
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
            None,
            "The two password fields didn't match.",
        ),
        # Test valid registration
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
            {"key": "mocked-access-token"},
            None,
        ),
    ],
)
@patch("dj_rest_auth.registration.views.allauth_account_settings.EMAIL_VERIFICATION")
@patch("dj_rest_auth.registration.views.RegisterView.get_response_data")
def test_register_user(
    mock_get_response_data,
    mock_send_email,
    api_client,
    register_data,
    expected_status,
    expected_data,
    expected_error_message,
    create_user,
):
    create_user("existing_email@example.com", "Sfrc.123", "existing_username")
    mock_get_response_data.return_value = {"key": "mocked-access-token"}
    response = send_request(
        api_client, method="post", url_name="rest_register", data=register_data
    )
    validate_response(
        response,
        expected_status,
        expected_data=expected_data,
        expected_error_message=expected_error_message,
    )


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
    create_user,
    key,
    expected_status,
    expected_error,
):
    user_data = {
        "email": "verifyuser@example.com",
        "username": "verifyuser",
        "password": "StrongPassword123",
    }

    user = create_user(
        email=user_data["email"],
        password=user_data["password"],
        username=user_data["username"],
        is_verified=False,
    )

    email_confirmation = user.emailaddress_set.get(
        email=user_data["email"]
    ).emailconfirmation_set.first()
    valid_key = email_confirmation.key if email_confirmation else None

    if key == "valid-key":
        key = valid_key

    response = send_request(api_client, "post", "rest_verify_email", data={"key": key})

    validate_response(
        response,
        expected_status=expected_status,
        expected_error_message=expected_error,
    )


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
    api_client, create_user, email, expected_status, expected_error
):
    user_data = {
        "email": "resenduser@example.com",
        "username": "resenduser",
        "password": "StrongPassword123",
    }

    create_user(
        email=user_data["email"],
        password=user_data["password"],
        username=user_data["username"],
        is_verified=False,
    )

    response = send_request(
        api_client, "post", "rest_resend_email", data={"email": email}
    )

    validate_response(
        response,
        expected_status=expected_status,
        expected_error_message=expected_error,
    )
    if expected_status == status.HTTP_200_OK:
        assert len(mail.outbox) > 0, "Expected at least one email to be sent."


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
    user = create_user(
        username="newuser", email="newuser@example.com", password="Sfrc.123"
    )
    user.emailaddress_set.update(verified=True)
    response = send_request(api_client, "post", "rest_login", data=login_data)
    validate_response(
        response,
        expected_status=expected_status,
        expected_error_message=expected_error_msg,
    )


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
def test_logout(api_client, create_user, auth_header, expected_status, expected_detail):
    create_user(username="newuser", email="newuser@example.com", password="Sfrc.123")
    login_data = {"username": "newuser", "password": "Sfrc.123"}
    response = send_request(api_client, "post", "token_obtain_pair", data=login_data)
    validate_response(
        response,
        expected_status=status.HTTP_200_OK,
    )

    token = response.data["access"]
    if auth_header:
        if "{token}" in auth_header:
            auth_header = auth_header.format(token=token)
        api_client.credentials(HTTP_AUTHORIZATION=auth_header)

    logout_response = send_request(api_client, "get", "rest_logout")
    validate_response(
        logout_response,
        expected_status=expected_status,
        expected_error_message=expected_detail,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_authenticated, new_password1, new_password2, expected_status, expected_detail",
    [
        (
            True,
            "new_person",
            "new_person",
            status.HTTP_200_OK,
            "New password has been saved.",
        ),
        (
            True,
            "new_person1",
            "new_person2",
            status.HTTP_400_BAD_REQUEST,
            "The two password fields didn’t match.",
        ),
        (
            True,
            "",
            "",
            status.HTTP_400_BAD_REQUEST,
            "This field may not be blank.",
        ),
        (
            True,
            "short",
            "short",
            status.HTTP_400_BAD_REQUEST,
            "This password is too short. It must contain at least 8 characters.",
        ),
        (
            True,
            "password123",
            "password123",
            status.HTTP_400_BAD_REQUEST,
            "This password is too common.",
        ),
        (
            False,
            "new_password",
            "new_password",
            status.HTTP_401_UNAUTHORIZED,
            "Authentication credentials were not provided.",
        ),
    ],
)
def test_change_password(
    api_client,
    create_user,
    is_authenticated,
    new_password1,
    new_password2,
    expected_status,
    expected_detail,
):

    user = create_user(
        username="testuser", email="test@example.com", password="Sher.654"
    )

    if is_authenticated:
        api_client.force_authenticate(user=user)

    change_password_url = reverse("rest_password_change")
    password_change_payload = {
        "new_password1": new_password1,
        "new_password2": new_password2,
    }
    response = api_client.post(change_password_url, data=password_change_payload)
    validate_response(
        response,
        expected_status=expected_status,
        expected_error_message=expected_detail,
    )


@pytest.mark.django_db
def test_change_password_unauthenticated(api_client):
    url = reverse("rest_password_change")
    data = {
        "old_password": "password123",
        "new_password1": "newpassword123",
        "new_password2": "newpassword123",
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.data


@pytest.mark.django_db
@patch("django.core.mail.EmailMessage.send")
@pytest.mark.parametrize(
    "username, email, reset_email, exists, is_active, expected_status, expected_detail, mock_email_called",
    [
        # Valid email, user exists, and is active - email should be sent.
        (
            "valid-email",
            "valid-email@example.com",
            "valid-email@example.com",
            True,
            True,
            200,
            "Password reset e-mail has been sent.",
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
            "This email address is not associated with any account.",
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
            "This field may not be blank.",
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
            "This account is inactive.",
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
            "Enter a valid email address.",
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
    expected_detail,
    mock_email_called,
):
    if exists:
        create_user(
            username=username,
            email=email,
            password="password123",
            is_active=is_active,
        )

    url = reverse("rest_password_reset")
    response = api_client.post(url, {"email": reset_email})

    response_data = response.json()

    validate_response(
        response,
        expected_status=expected_status,
        expected_error_message=expected_detail,
    )

    if mock_email_called:
        mock_email_send.assert_called_once()
    else:
        mock_email_send.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "uid_modifier, token_modifier, new_password1, new_password2, expected_status, expected_detail",
    [
        (
            "valid_uid",
            "valid_token",
            "newpassword123",
            "newpassword123",
            200,
            "Password has been reset with the new password.",
        ),
        (
            "invalid_uid",
            "valid_token",
            "newpassword123",
            "newpassword123",
            400,
            {"uid": ["Invalid value"]},
        ),
        (
            "valid_uid",
            "invalid_token",
            "newpassword123",
            "newpassword123",
            400,
            {"token": ["Invalid value"]},
        ),
        (
            "valid_uid",
            "valid_token",
            "newpassword123",
            "differentpassword",
            400,
            {"new_password2": ["The two password fields didn’t match."]},
        ),
        (
            None,
            "valid_token",
            "newpassword123",
            "newpassword123",
            400,
            {"uid": ["This field is required."]},
        ),
        (
            "valid_uid",
            None,
            "newpassword123",
            "newpassword123",
            400,
            {"token": ["This field is required."]},
        ),
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

    user = create_user(
        username="testuser", email="test@example.com", password="oldpassword123"
    )
    response = send_request(
        api_client, "post", "rest_password_reset", data={"email": user.email}
    )
    validate_response(response, status.HTTP_200_OK)

    email_body = mail.outbox[0].body
    reset_url = email_body.split("password-reset/confirm/")[1]
    valid_uid, valid_token = reset_url.split("/")[:2]

    uid = valid_uid if uid_modifier == "valid_uid" else uid_modifier
    token = valid_token if token_modifier == "valid_token" else token_modifier

    payload = {
        "uid": uid,
        "token": token,
        "new_password1": new_password1,
        "new_password2": new_password2,
    }
    payload = {key: value for key, value in payload.items() if value is not None}

    response = send_request(
        api_client, "post", "rest_password_reset_confirm", data=payload
    )
    validate_response(response, expected_status, expected_error_message=expected_detail)
