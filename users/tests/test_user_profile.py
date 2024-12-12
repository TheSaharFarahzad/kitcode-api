from PIL import Image
import io
import pytest
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from .conftest import send_request, validate_response, authenticate_user

import tempfile
import shutil
import pytest
from django.test import override_settings
from PIL import Image
import io
from django.core.files.uploadedfile import SimpleUploadedFile

# Create a valid in-memory image file for testing
image_data = io.BytesIO()
image = Image.new("RGB", (100, 100), color="red")
image.save(image_data, format="JPEG")
image_data.seek(0)

# Temporary directory for media files during tests
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@pytest.fixture(scope="function", autouse=True)
def setup_media_storage():
    with override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT):
        yield
    # Cleanup the temporary media directory after the test
    shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_authenticated, expected_status, expected_response_keys",
    [
        # Authenticated user
        (
            True,
            status.HTTP_200_OK,
            {"username", "email", "first_name", "last_name"},
        ),
        # Unauthenticated user
        (
            False,
            status.HTTP_401_UNAUTHORIZED,
            set(),
        ),
    ],
)
def test_get_user(
    api_client, create_user, is_authenticated, expected_status, expected_response_keys
):

    user = create_user(email="user@test.com", username="testuser", password="testpass")
    if is_authenticated:
        authenticate_user(api_client, user)

    response = send_request(api_client, "get", "rest_user_details")

    expected_data = None
    expected_error_message = (
        "Authentication credentials were not provided."
        if not is_authenticated
        else None
    )

    if expected_status == status.HTTP_200_OK:
        expected_data = {
            "username": user.username,
            "email": user.email,
        }

    validate_response(
        response,
        expected_status,
        expected_data=expected_data,
        expected_error_message=expected_error_message,
    )


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

    user = create_user(email="user@test.com", username="testuser", password="testpass")
    if is_authenticated:
        api_client.force_authenticate(user=user)

    response = send_request(
        api_client, method="put", url_name="rest_user_details", data=request_data
    )

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

    user = create_user(email="user@test.com", username="testuser", password="testpass")
    if is_authenticated:
        api_client.force_authenticate(user=user)

    response = send_request(
        api_client, method="put", url_name="rest_user_details", data=request_data
    )

    assert (
        response.status_code == expected_status
    ), f"Expected status {expected_status}, but got {response.status_code}"

    if expected_status == status.HTTP_400_BAD_REQUEST:
        assert (
            response.data == expected_response_data
        ), f"Expected error data {expected_response_data}, but got {response.data}"
    elif expected_status == status.HTTP_200_OK:
        assert response.data["picture"].startswith(
            "http://testserver/media/profile_pics/"
        ), f"Expected picture URL to start with 'http://testserver/media/profile_pics/', but got {response.data['picture']}"
