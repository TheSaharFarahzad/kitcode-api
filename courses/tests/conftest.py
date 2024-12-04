import pytest
import random
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from courses.models import Course, Lesson, UserRole


# API client fixture
@pytest.fixture
def api_client():
    """Provides an instance of APIClient."""
    return APIClient()


# Fixture to create a user dynamically
@pytest.fixture
def create_user(db):
    """Fixture to create a new user with a unique username."""

    def _create_user(username, email, password, is_active=True):
        User = get_user_model()

        # Ensure unique username by appending a random string
        unique_username = f"{username}_{random.randint(1000, 9999)}"

        user = User.objects.create_user(
            username=unique_username, email=email, password=password
        )
        user.is_active = is_active
        user.save()
        return user

    return _create_user


# Fixture to create a course dynamically
@pytest.fixture
def create_course(db):
    """Fixture to create a new course with a unique title."""

    def _create_course(instructor_user, title, description, is_published=False):
        course = Course.objects.create(
            created_by=instructor_user,
            title=title,
            description=description,
            is_published=is_published,
        )
        return course

    return _create_course


# Fixture to create a lesson dynamically
@pytest.fixture
def create_lesson(db):
    """Fixture to create a new lesson for a course."""

    def _create_lesson(course, title, content="Lesson Content", order=1):
        lesson = Lesson.objects.create(
            course=course,
            title=title,
            content=content,
            order=order,
        )
        return lesson

    return _create_lesson


# Fixture to create all necessary users and courses
@pytest.fixture
def setup_users_and_courses(create_user, create_course, create_lesson):
    """Fixture to create users, courses, and lessons."""

    # Create users
    regular_user = create_user(
        "regular_user",
        "regular_user@example.com",
        "1234.qaz",
    )
    instructor_user = create_user(
        "instructor_user",
        "instructor@example.com",
        "1234.qaz",
    )
    another_instructor = create_user(
        "another_instructor",
        "another_instructor@example.com",
        "1234.qaz",
    )
    student_user = create_user(
        "student_user",
        "student@example.com",
        "1234.qaz",
    )
    another_student = create_user(
        "another_student",
        "another_student@example.com",
        "1234.qaz",
    )

    # Create courses
    course1 = create_course(
        instructor_user,
        "Course 1",
        "Introduction to Django.",
        is_published=True,
    )
    course2 = create_course(
        instructor_user,
        "Course 2",
        "Advanced Django.",
        is_published=False,
    )
    course3 = create_course(
        instructor_user,
        "Course 3",
        "Python for Beginners.",
        is_published=True,
    )

    # Enroll students in courses
    course1.enroll_student(student_user)
    course2.enroll_student(another_student)

    # Create lessons for courses
    lesson1 = create_lesson(course1, "Lesson 1", "Django Basics", order=1)
    lesson2 = create_lesson(course1, "Lesson 2", "Django Models", order=2)
    lesson3 = create_lesson(course2, "Lesson 1", "Advanced Django Topics", order=1)
    lesson4 = create_lesson(course3, "Lesson 1", "Python Basics", order=1)

    # Return the users, courses, and lessons for use in tests
    return {
        "regular_user": regular_user,
        "instructor_user": instructor_user,
        "another_instructor": another_instructor,
        "student_user": student_user,
        "another_student": another_student,
        "course1": course1,
        "course2": course2,
        "course3": course3,
        "lesson1": lesson1,
        "lesson2": lesson2,
        "lesson3": lesson3,
        "lesson4": lesson4,
    }
