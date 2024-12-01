import pytest
from rest_framework import status
from django.urls import reverse
from courses.models import Lesson


@pytest.mark.parametrize(
    "user_role, is_authenticated, expected_status, expected_count, expected_detail",
    [
        (
            None,
            False,
            status.HTTP_401_UNAUTHORIZED,
            0,
            "Authentication credentials were not provided.",
        ),
        (
            "regular_user",
            True,
            status.HTTP_403_FORBIDDEN,
            0,
            "You do not have permission to perform this action.",
        ),
        (
            "student_user",
            True,
            status.HTTP_200_OK,
            2,
            None,
        ),
        (
            "another_student",
            True,
            status.HTTP_403_FORBIDDEN,
            0,
            "You do not have permission to perform this action.",
        ),
        (
            "instructor_user",
            True,
            status.HTTP_200_OK,
            2,
            None,
        ),
        (
            "another_instructor",
            True,
            status.HTTP_403_FORBIDDEN,
            0,
            "You do not have permission to perform this action.",
        ),
    ],
)
def test_list_lessons(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    expected_status,
    expected_count,
    expected_detail,
):
    # Get the users and courses from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    student_user = setup_users_and_courses["student_user"]
    another_student = setup_users_and_courses["another_student"]
    instructor_user = setup_users_and_courses["instructor_user"]
    another_instructor = setup_users_and_courses["another_instructor"]
    course1 = setup_users_and_courses["course1"]

    # Ensure the instructor_user is the creator and assigned the instructor role for course1
    course1.created_by = instructor_user
    course1.assign_instructor(instructor_user)
    course1.save()

    # Map roles to user instances, including the new 'another_student' role
    user_map = {
        "unauthenticated_user": None,
        "regular_user": regular_user,
        "student_user": student_user,
        "another_student": another_student,
        "instructor_user": instructor_user,
        "another_instructor": another_instructor,
    }

    # Authenticate user based on role
    user_instance = user_map.get(user_role, None)
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    # Use the primary key of the first course as an example
    course_id = course1.id
    url = reverse("course-lessons-list", kwargs={"course_pk": course_id})

    response = api_client.get(url)
    assert response.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        assert len(response.data) == expected_count
    else:
        assert expected_detail in str(response.data)


@pytest.mark.parametrize(
    "user_role, is_authenticated, expected_status, expected_title, expected_detail",
    [
        (
            None,
            False,
            status.HTTP_401_UNAUTHORIZED,
            None,
            "Authentication credentials were not provided.",
        ),
        (
            "regular_user",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "student_user",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "Only the instructor of the course can create lessons.",
        ),
        (
            "another_student",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "instructor_user",
            True,
            status.HTTP_201_CREATED,
            "New Lesson",
            None,
        ),
        (
            "another_instructor",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
    ],
)
def test_create_lesson(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    expected_status,
    expected_title,
    expected_detail,
):
    # Get the users and courses from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    student_user = setup_users_and_courses["student_user"]
    another_student = setup_users_and_courses["another_student"]
    instructor_user = setup_users_and_courses["instructor_user"]
    another_instructor = setup_users_and_courses["another_instructor"]
    course1 = setup_users_and_courses["course1"]

    # Ensure the instructor_user is the creator and assigned the instructor role for course1
    course1.created_by = instructor_user
    course1.assign_instructor(instructor_user)
    course1.save()

    # Map roles to user instances, including the new 'another_student' role
    user_map = {
        "unauthenticated_user": None,
        "regular_user": regular_user,
        "student_user": student_user,
        "another_student": another_student,
        "instructor_user": instructor_user,
        "another_instructor": another_instructor,
    }

    # Authenticate user based on role
    user_instance = user_map.get(user_role, None)
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    url = reverse("course-lessons-list", kwargs={"course_pk": course1.id})

    # Include the course dynamically in the data payload
    data = {
        "title": "New Lesson",
        "content": "Content",
        "order": 3,
        "course": course1.id,
    }

    # Attempt to create a lesson
    response = api_client.post(url, data=data)
    assert response.status_code == expected_status

    if expected_status == status.HTTP_201_CREATED:
        # Validate the title of the created lesson
        assert response.data["title"] == expected_title
    else:
        assert expected_detail in str(response.data)


@pytest.mark.parametrize(
    "user_role, is_authenticated, expected_status, expected_title, expected_detail",
    [
        (
            None,
            False,
            status.HTTP_401_UNAUTHORIZED,
            None,
            "Authentication credentials were not provided.",
        ),
        (
            "regular_user",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "student_user",
            True,
            status.HTTP_200_OK,
            "Lesson 1",
            None,
        ),
        (
            "another_student",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "instructor_user",
            True,
            status.HTTP_200_OK,
            "Lesson 1",
            None,
        ),
        (
            "another_instructor",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
    ],
)
def test_retrieve_lesson(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    expected_status,
    expected_title,
    expected_detail,
):

    # Get the users and courses from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    student_user = setup_users_and_courses["student_user"]
    another_student = setup_users_and_courses["another_student"]
    instructor_user = setup_users_and_courses["instructor_user"]
    another_instructor = setup_users_and_courses["another_instructor"]
    course1 = setup_users_and_courses["course1"]
    lesson1 = setup_users_and_courses["lesson1"]

    # Ensure the instructor_user is the creator and assigned the instructor role for course1
    course1.created_by = instructor_user
    course1.assign_instructor(instructor_user)
    course1.save()

    # Ensure the lesson is associated with the course and instructor
    lesson1.course = course1
    lesson1.save()

    # Map roles to user instances, including the new 'another_student' role
    user_map = {
        "unauthenticated_user": None,
        "regular_user": regular_user,
        "student_user": student_user,
        "another_student": another_student,
        "instructor_user": instructor_user,
        "another_instructor": another_instructor,
    }

    # Authenticate user based on role
    user_instance = user_map.get(user_role, None)
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    url = reverse(
        "course-lessons-detail", kwargs={"course_pk": course1.id, "pk": lesson1.id}
    )

    # Attempt to retrieve the lesson
    response = api_client.get(url)
    assert response.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        assert response.data["title"] == expected_title
    else:
        assert expected_detail in str(response.data)


@pytest.mark.parametrize(
    "user_role, is_authenticated, expected_status, expected_title, expected_detail",
    [
        (
            None,
            False,
            status.HTTP_401_UNAUTHORIZED,
            None,
            "Authentication credentials were not provided.",
        ),
        (
            "regular_user",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "student_user",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "another_student",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "instructor_user",
            True,
            status.HTTP_200_OK,
            "Updated Lesson Title",
            None,
        ),
        (
            "another_instructor",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
    ],
)
def test_update_lesson(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    expected_status,
    expected_title,
    expected_detail,
):

    # Get the users and courses from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    student_user = setup_users_and_courses["student_user"]
    another_student = setup_users_and_courses["another_student"]
    instructor_user = setup_users_and_courses["instructor_user"]
    another_instructor = setup_users_and_courses["another_instructor"]
    course1 = setup_users_and_courses["course1"]
    lesson1 = setup_users_and_courses["lesson1"]

    # Ensure the instructor_user is the creator and assigned the instructor role for course1
    course1.created_by = instructor_user
    course1.assign_instructor(instructor_user)
    course1.save()

    # Ensure the lesson is associated with the course and instructor
    lesson1.course = course1
    lesson1.save()

    # Map roles to user instances, including the new 'another_student' role
    user_map = {
        "unauthenticated_user": None,
        "regular_user": regular_user,
        "student_user": student_user,
        "another_student": another_student,
        "instructor_user": instructor_user,
        "another_instructor": another_instructor,
    }

    # Authenticate user based on role
    user_instance = user_map.get(user_role, None)
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    url = reverse(
        "course-lessons-detail", kwargs={"course_pk": course1.id, "pk": lesson1.id}
    )

    # Data for updating the lesson
    data = {
        "title": "Updated Lesson Title",
        "content": "Updated Content",
        "order": 3,
        "course": course1.id,
    }

    # Attempt to update the lesson
    response = api_client.put(url, data=data)
    assert response.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        assert response.data["title"] == expected_title
    else:
        assert expected_detail in str(response.data)


@pytest.mark.parametrize(
    "user_role, is_authenticated, expected_status, expected_title, expected_detail",
    [
        (
            None,
            False,
            status.HTTP_401_UNAUTHORIZED,
            None,
            "Authentication credentials were not provided.",
        ),
        (
            "regular_user",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "student_user",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "another_student",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
        (
            "instructor_user",
            True,
            status.HTTP_200_OK,
            "Updated Lesson Title",
            None,
        ),
        (
            "another_instructor",
            True,
            status.HTTP_403_FORBIDDEN,
            None,
            "You do not have permission to perform this action.",
        ),
    ],
)
def test_partial_update_lesson(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    expected_status,
    expected_title,
    expected_detail,
):

    # Get the users and courses from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    student_user = setup_users_and_courses["student_user"]
    another_student = setup_users_and_courses["another_student"]
    instructor_user = setup_users_and_courses["instructor_user"]
    another_instructor = setup_users_and_courses["another_instructor"]
    course1 = setup_users_and_courses["course1"]
    lesson1 = setup_users_and_courses["lesson1"]

    # Ensure the instructor_user is the creator and assigned the instructor role for course1
    course1.created_by = instructor_user
    course1.assign_instructor(instructor_user)
    course1.save()

    # Ensure the lesson is associated with the course and instructor
    lesson1.course = course1
    lesson1.save()

    # Map roles to user instances, including the new 'another_student' role
    user_map = {
        "unauthenticated_user": None,
        "regular_user": regular_user,
        "student_user": student_user,
        "another_student": another_student,
        "instructor_user": instructor_user,
        "another_instructor": another_instructor,
    }

    # Authenticate user based on role
    user_instance = user_map.get(user_role, None)
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    url = reverse(
        "course-lessons-detail", kwargs={"course_pk": course1.id, "pk": lesson1.id}
    )

    # Data for partially updating the lesson
    data = {
        "title": "Updated Lesson Title",
        "content": "Updated Content",
        "order": 3,
        "course": course1.id,
    }

    # Attempt to update the lesson with PATCH request
    response = api_client.patch(url, data=data)
    assert response.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        assert response.data["title"] == expected_title
    else:
        assert expected_detail in str(response.data)


@pytest.mark.parametrize(
    "user_role, is_authenticated, expected_status, expected_detail",
    [
        (
            None,
            False,
            status.HTTP_401_UNAUTHORIZED,
            "Authentication credentials were not provided.",
        ),
        (
            "regular_user",
            True,
            status.HTTP_403_FORBIDDEN,
            "You do not have permission to perform this action.",
        ),
        (
            "student_user",
            True,
            status.HTTP_403_FORBIDDEN,
            "You do not have permission to perform this action.",
        ),
        (
            "another_student",
            True,
            status.HTTP_403_FORBIDDEN,
            "You do not have permission to perform this action.",
        ),
        (
            "instructor_user",
            True,
            status.HTTP_204_NO_CONTENT,
            None,
        ),
        (
            "another_instructor",
            True,
            status.HTTP_403_FORBIDDEN,
            "You do not have permission to perform this action.",
        ),
    ],
)
def test_delete_lesson(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    expected_status,
    expected_detail,
):

    # Get the users and courses from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    student_user = setup_users_and_courses["student_user"]
    another_student = setup_users_and_courses["another_student"]
    instructor_user = setup_users_and_courses["instructor_user"]
    another_instructor = setup_users_and_courses["another_instructor"]
    course1 = setup_users_and_courses["course1"]
    lesson1 = setup_users_and_courses["lesson1"]

    # Ensure the instructor_user is the creator and assigned the instructor role for course1
    course1.created_by = instructor_user
    course1.assign_instructor(instructor_user)
    course1.save()

    # Ensure the lesson is associated with the course and instructor
    lesson1.course = course1
    lesson1.save()

    # Map roles to user instances, including the new 'another_student' role
    user_map = {
        "unauthenticated_user": None,
        "regular_user": regular_user,
        "student_user": student_user,
        "another_student": another_student,
        "instructor_user": instructor_user,
        "another_instructor": another_instructor,
    }

    # Authenticate user based on role
    user_instance = user_map.get(user_role, None)
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    url = reverse(
        "course-lessons-detail", kwargs={"course_pk": course1.id, "pk": lesson1.id}
    )

    # Attempt to delete the lesson
    response = api_client.delete(url)
    assert response.status_code == expected_status

    if expected_status == status.HTTP_204_NO_CONTENT:
        # If the delete is successful, ensure the lesson is removed from the database
        assert not Lesson.objects.filter(id=lesson1.id).exists()
    else:
        # Ensure that the expected detail is returned when deletion is not allowed
        assert expected_detail in str(response.data)
