# Standard library imports
import io
from unittest.mock import patch

# Third-party imports
from PIL import Image
import pytest
from rest_framework import status

# Django imports
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

# Local imports
from .conftest import send_request, validate_response

# Create a valid in-memory image file for testing
image_data = io.BytesIO()
image = Image.new("RGB", (100, 100), color="red")
image.save(image_data, format="JPEG")
image_data.seek(0)


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
    # Arrange
    create_user("existing_email@example.com", "Sfrc.123", "existing_username")

    # Mock
    mock_get_response_data.return_value = {"key": "mocked-access-token"}

    # Act
    response = send_request(
        api_client, method="post", url_name="rest_register", data=register_data
    )

    # Assert
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
@pytest.mark.parametrize(
    "is_authenticated, request_data, expected_status, expected_response_data",
    [
        # Unauthenticated user
        (
            False,
            {
                "username": "updateduser",
                "email": "updateduser@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
            status.HTTP_401_UNAUTHORIZED,
            {"detail": "Authentication credentials were not provided."},
        ),
        # Authenticated user, valid data
        (
            True,
            {
                "username": "updateduser",
                "email": "updateduser@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
            status.HTTP_200_OK,
            {
                "username": "updateduser",
                "email": "updateduser@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
        ),
        # Authenticated user, omit username
        (
            True,
            {
                "username": "",
                "email": "updateduser@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
            status.HTTP_200_OK,
            {
                "username": "testuser",
                "email": "updateduser@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
        ),
        # Authenticated user, empty username
        (
            True,
            {
                "email": "updateduser@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
            status.HTTP_200_OK,
            {
                "username": "testuser",
                "email": "updateduser@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
        ),
        # Authenticated user, omit email
        (
            True,
            {
                "username": "updateduser",
                "email": "",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
            status.HTTP_200_OK,
            {
                "username": "updateduser",
                "email": "user@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
        ),
        # Authenticated user, empty email
        (
            True,
            {
                "username": "updateduser",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
            status.HTTP_200_OK,
            {
                "username": "updateduser",
                "email": "user@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
        ),
        # Authenticated user, username exists
        (
            True,
            {
                "username": "testuser",
                "email": "updateduser@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
            status.HTTP_200_OK,
            {
                "username": "testuser",
                "email": "updateduser@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
        ),
        # Authenticated user, email exists
        (
            True,
            {
                "username": "updateduser",
                "email": "user@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
            status.HTTP_200_OK,
            {
                "username": "updateduser",
                "email": "user@test.com",
                "first_name": "Updated",
                "last_name": "User",
                "bio": "This is the bio",
            },
        ),
        # Authenticated user, omit all data
        (
            True,
            {
                "username": "",
                "email": "",
                "first_name": "",
                "last_name": "",
                "bio": "",
            },
            status.HTTP_200_OK,
            {
                "username": "testuser",
                "email": "user@test.com",
                "first_name": "",
                "last_name": "",
                "bio": "",
            },
        ),
        # Authenticated user, empty all data
        (
            True,
            {},
            status.HTTP_200_OK,
            {
                "username": "testuser",
                "email": "user@test.com",
                "first_name": "",
                "last_name": "",
                "bio": "",
            },
        ),
    ],
)
def test_update_user(
    api_client,
    create_user,
    is_authenticated,
    request_data,
    expected_status,
    expected_response_data,
):
    # Arrange
    user = create_user(email="user@test.com", username="testuser", password="testpass")
    if is_authenticated:
        api_client.force_authenticate(user=user)

    # Act
    response = send_request(
        api_client, method="put", url_name="rest_user_details", data=request_data
    )

    # Assert
    if expected_status == status.HTTP_200_OK:
        expected_response_data["id"] = user.id
    validate_response(response, expected_status, expected_response_data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_authenticated, request_data, expected_status, expected_response_data",
    [
        # Authenticated user, valid image type (JPEG)
        (
            True,
            {
                "picture": SimpleUploadedFile(
                    name="valid-image.jpeg",
                    content=image_data.getvalue(),
                    content_type="image/jpeg",
                )
            },
            status.HTTP_200_OK,
            {"picture": "http://testserver/media/profile_pics/valid-image.jpeg"},
        ),
        # Authenticated user, valid image type (JPG)
        (
            True,
            {
                "picture": SimpleUploadedFile(
                    name="valid-image.jpg",
                    content=image_data.getvalue(),
                    content_type="image/jpg",
                )
            },
            status.HTTP_200_OK,
            {"picture": "http://testserver/media/profile_pics/valid-image.jpg"},
        ),
        # Authenticated user, valid image type (PNG)
        (
            True,
            {
                "picture": SimpleUploadedFile(
                    name="valid-image.png",
                    content=image_data.getvalue(),
                    content_type="image/png",
                )
            },
            status.HTTP_200_OK,
            {"picture": "http://testserver/media/profile_pics/valid-image.png"},
        ),
        # Authenticated user, invalid image (text file)
        (
            True,
            {
                "picture": SimpleUploadedFile(
                    name="not-an-image.txt",
                    content=b"This is not an image",
                    content_type="text/plain",
                )
            },
            status.HTTP_400_BAD_REQUEST,
            {
                "picture": [
                    "Upload a valid image. The file you uploaded was either not an image or a corrupted image."
                ]
            },
        ),
        # Authenticated user, invalid image (string type)
        (
            True,
            {"picture": "string"},
            status.HTTP_400_BAD_REQUEST,
            {
                "picture": [
                    "The submitted data was not a file. Check the encoding type on the form."
                ]
            },
        ),
    ],
)
def test_update_user_profile_picture(
    api_client,
    create_user,
    is_authenticated,
    request_data,
    expected_status,
    expected_response_data,
):
    # Arrange
    user = create_user(email="user@test.com", username="testuser", password="testpass")
    if is_authenticated:
        api_client.force_authenticate(user=user)

    # Act
    response = send_request(
        api_client, method="put", url_name="rest_user_details", data=request_data
    )

    # Assert status code
    assert (
        response.status_code == expected_status
    ), f"Expected status {expected_status}, but got {response.status_code}"

    # Validate the response data
    if expected_status == status.HTTP_400_BAD_REQUEST:
        assert (
            response.data == expected_response_data
        ), f"Expected error data {expected_response_data}, but got {response.data}"
    elif expected_status == status.HTTP_200_OK:
        # Check if picture URL is correct and matches the expected response format
        assert response.data["picture"].startswith(
            "http://testserver/media/profile_pics/"
        ), f"Expected picture URL to start with 'http://testserver/media/profile_pics/', but got {response.data['picture']}"
