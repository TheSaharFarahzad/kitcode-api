import pytest
from django.urls import reverse
from rest_framework import status
from courses.models import Course, UserRole
import pytest
from rest_framework import status
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_role, is_authenticated, expected_courses, num_courses",
    [
        # Not logged in user (can only see published courses)
        (
            "unauthenticated_user",
            False,
            ["Course 1", "Course 3"],
            2,
        ),
        # Logged-in regular user (can only see published courses)
        (
            "regular_user",
            True,
            ["Course 1", "Course 3"],
            2,
        ),
        # Logged-in student (can only see published courses)
        (
            "student_user",
            True,
            ["Course 1", "Course 3"],
            2,
        ),
        # Logged-in instructor of another course (can only see published courses)
        (
            "another_instructor",
            True,
            ["Course 1", "Course 3"],
            2,
        ),
        # Logged-in instructor of this course (can see all courses they created, including unpublished ones)
        (
            "instructor_user",
            True,
            ["Course 1", "Course 2", "Course 3"],
            3,
        ),
    ],
)
def test_course_list(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    expected_courses,
    num_courses,
):
    # Get the users and courses from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    instructor_user = setup_users_and_courses["instructor_user"]
    another_instructor = setup_users_and_courses["another_instructor"]
    student_user = setup_users_and_courses["student_user"]
    course1 = setup_users_and_courses["course1"]
    course2 = setup_users_and_courses["course2"]
    course3 = setup_users_and_courses["course3"]

    # Map roles to user instances
    user_map = {
        "regular_user": regular_user,
        "instructor_user": instructor_user,
        "another_instructor": another_instructor,
        "student_user": student_user,
        "unauthenticated_user": None,
    }

    # Authenticate user based on the role
    user_instance = user_map[user_role]
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    url = reverse("course-list")

    # Send GET request to the course list endpoint
    response = api_client.get(url)

    # Check response
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == num_courses

    # Verify that the expected courses are in the response
    for course_title in expected_courses:
        assert any(course["title"] == course_title for course in response.data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_role, is_authenticated, data, expected_status, expected_role",
    [
        (
            "instructor_user",
            True,
            {
                "title": "New Course",
                "description": "Course Description",
                "is_published": True,
            },
            status.HTTP_201_CREATED,
            "instructor",
        ),
        (
            "student_user",
            True,
            {
                "title": "Unauthorized Course",
                "description": "Unauthorized Course Description",
                "is_published": True,
            },
            status.HTTP_201_CREATED,
            "instructor",
        ),
        (
            "regular_user",
            True,
            {
                "title": "Regular User Course",
                "description": "Regular User Course Description",
                "is_published": True,
            },
            status.HTTP_201_CREATED,
            "instructor",
        ),
        (
            "unauthenticated_user",
            False,
            {
                "title": "Unauth Course",
                "description": "Unauth Course Desc",
                "is_published": True,
            },
            status.HTTP_401_UNAUTHORIZED,
            None,
        ),
    ],
)
def test_course_creation(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    data,
    expected_status,
    expected_role,
):
    # Get users from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    instructor_user = setup_users_and_courses["instructor_user"]
    student_user = setup_users_and_courses["student_user"]

    # Map roles to user instances
    user_map = {
        "regular_user": regular_user,
        "instructor_user": instructor_user,
        "student_user": student_user,
        "unauthenticated_user": None,
    }

    # Authenticate user based on role
    user_instance = user_map[user_role]
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)
    else:
        api_client.force_authenticate(user=None)

    # Send POST request to create a course
    response = api_client.post(reverse("course-list"), data, format="json")

    # Check the response status code
    assert response.status_code == expected_status

    # Additional checks for successful creation
    if expected_status == status.HTTP_201_CREATED:
        course = Course.objects.get(id=response.data["id"])
        assert course.title == data["title"]
        assert course.description == data["description"]

        # Verify the user's role for the created course
        user_role_association = UserRole.objects.filter(
            user=course.created_by, course=course
        ).first()
        assert user_role_association is not None
        assert user_role_association.role == expected_role

        # Check if the instructor role is assigned for published courses
        if course.is_published:
            user_role_association.refresh_from_db()
            assert user_role_association.role == "instructor"

    # Ensure no course is created for unauthorized access
    else:
        assert Course.objects.filter(title=data["title"]).count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_role, is_authenticated, data, expected_status, expected_title",
    [
        (
            "instructor_user",
            True,
            {"title": "Updated Course Title", "description": "Updated Description"},
            status.HTTP_200_OK,
            "Updated Course Title",
        ),
        (
            "student_user",
            True,
            {"title": "Student Attempted Update", "description": "Updated Description"},
            status.HTTP_403_FORBIDDEN,
            None,
        ),
        (
            "regular_user",
            True,
            {
                "title": "Regular User Attempted Update",
                "description": "Updated Description",
            },
            status.HTTP_403_FORBIDDEN,
            None,
        ),
        (
            "unauthenticated_user",
            False,
            {
                "title": "Unauthenticated Attempted Update",
                "description": "Updated Description",
            },
            status.HTTP_401_UNAUTHORIZED,
            None,
        ),
    ],
)
def test_course_update(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    data,
    expected_status,
    expected_title,
):
    # Get the users and courses from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    instructor_user = setup_users_and_courses["instructor_user"]
    another_instructor = setup_users_and_courses["another_instructor"]
    student_user = setup_users_and_courses["student_user"]
    course1 = setup_users_and_courses["course1"]
    course2 = setup_users_and_courses["course2"]
    course3 = setup_users_and_courses["course3"]

    # Ensure the instructor_user is the creator and assigned the instructor role for course1
    course1.created_by = instructor_user
    course1.assign_instructor(instructor_user)
    course1.save()

    # Map roles to user instances
    user_map = {
        "regular_user": regular_user,
        "instructor_user": instructor_user,
        "student_user": student_user,
        "unauthenticated_user": None,
    }

    # Authenticate user based on role
    user_instance = user_map[user_role]
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    url = reverse("course-detail", kwargs={"pk": course1.id})

    # Send PUT request to update the course
    response = api_client.put(url, data, format="json")

    # Check response status
    assert response.status_code == expected_status

    # Verify that the course title is updated if the update was successful
    if expected_status == status.HTTP_200_OK:
        course = Course.objects.get(id=course1.id)
        assert course.title == expected_title


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_role, is_authenticated, data, expected_status, expected_title",
    [
        (
            "instructor_user",
            True,
            {"title": "Updated Course Title", "description": "Updated Description"},
            status.HTTP_200_OK,
            "Updated Course Title",
        ),
        (
            "student_user",
            True,
            {"title": "Student Attempted Update", "description": "Updated Description"},
            status.HTTP_403_FORBIDDEN,
            None,
        ),
        (
            "regular_user",
            True,
            {
                "title": "Regular User Attempted Update",
                "description": "Updated Description",
            },
            status.HTTP_403_FORBIDDEN,
            None,
        ),
        (
            "unauthenticated_user",
            False,
            {
                "title": "Unauthenticated Attempted Update",
                "description": "Updated Description",
            },
            status.HTTP_401_UNAUTHORIZED,
            None,
        ),
    ],
)
def test_course_patch_update(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    data,
    expected_status,
    expected_title,
):
    # Get the users and courses from the fixture
    regular_user = setup_users_and_courses["regular_user"]
    instructor_user = setup_users_and_courses["instructor_user"]
    student_user = setup_users_and_courses["student_user"]
    course1 = setup_users_and_courses["course1"]

    # Ensure the instructor_user is the creator and assigned the instructor role for course1
    course1.created_by = instructor_user
    course1.assign_instructor(instructor_user)
    course1.save()

    # Map roles to user instances
    user_map = {
        "regular_user": regular_user,
        "instructor_user": instructor_user,
        "student_user": student_user,
        "unauthenticated_user": None,
    }

    # Authenticate user based on role
    user_instance = user_map[user_role]
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    url = reverse("course-detail", kwargs={"pk": course1.id})

    # Send PATCH request to update the course
    response = api_client.patch(url, data, format="json")

    # Check response status
    assert response.status_code == expected_status

    # Verify that the course title is updated if the update was successful
    if expected_status == status.HTTP_200_OK:
        course = Course.objects.get(id=course1.id)
        assert course.title == expected_title


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_role, is_authenticated, expected_status",
    [
        (
            "instructor_user",
            True,
            status.HTTP_204_NO_CONTENT,
        ),
        (
            "student_user",
            True,
            status.HTTP_403_FORBIDDEN,
        ),
        (
            "regular_user",
            True,
            status.HTTP_403_FORBIDDEN,
        ),
        (
            "unauthenticated_user",
            False,
            status.HTTP_401_UNAUTHORIZED,
        ),
    ],
)
def test_course_delete(
    api_client,
    setup_users_and_courses,
    user_role,
    is_authenticated,
    expected_status,
):
    # Get the users and courses from the fixture
    instructor_user = setup_users_and_courses["instructor_user"]
    student_user = setup_users_and_courses["student_user"]
    regular_user = setup_users_and_courses["regular_user"]
    course1 = setup_users_and_courses["course1"]

    # Ensure the instructor_user is the creator and assigned the instructor role for course1
    course1.created_by = instructor_user
    course1.assign_instructor(instructor_user)
    course1.save()

    # Map roles to user instances
    user_map = {
        "regular_user": regular_user,
        "instructor_user": instructor_user,
        "student_user": student_user,
        "unauthenticated_user": None,
    }

    # Authenticate user based on role
    user_instance = user_map[user_role]
    if is_authenticated and user_instance:
        api_client.force_authenticate(user=user_instance)

    url = reverse("course-detail", kwargs={"pk": course1.id})

    # Send DELETE request to delete the course
    response = api_client.delete(url)

    # Check response status
    assert response.status_code == expected_status

    # If the request was successful (204), verify the course is deleted
    if expected_status == status.HTTP_204_NO_CONTENT:
        assert not Course.objects.filter(id=course1.id).exists()
