import pytest
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, UserRole
from django.core.exceptions import ValidationError


User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    """Fixture to create a test user."""
    return User.objects.create_user(
        username="test_user",
        email="test_user@test.com",
        password="testpassword",
    )


@pytest.fixture
def course(user):
    """Fixture to create a test course."""
    return Course.objects.create(
        title="Test Course",
        description="This is a test course.",
        created_by=user,
    )


@pytest.fixture
def lesson(course):
    """Fixture to create a test lesson."""
    return Lesson.objects.create(
        course=course,
        title="Test Lesson",
        content="Content of the test lesson.",
        order=1,
    )


@pytest.mark.parametrize(
    "title, description, should_raise",
    [
        (
            "Valid Course",
            "Valid description",
            False,
        ),
        (
            "",
            "Valid description",
            True,
        ),
        (
            "Valid Course",
            "",
            True,
        ),
    ],
)
def test_course_validation(user, title, description, should_raise):
    """
    Test course validation for various title and description combinations.
    """
    course = Course(
        title=title,
        description=description,
        created_by=user,
    )
    if should_raise:
        with pytest.raises(ValidationError):
            course.full_clean()
    else:
        course.full_clean()


def test_course_publish(user):
    """
    Test publishing a course assigns the instructor role.
    """
    course = Course.objects.create(
        title="Test Course", description="A course to test publishing.", created_by=user
    )
    assert not course.is_published

    course.publish()
    assert course.is_published
    assert UserRole.objects.filter(
        user=user, course=course, role=UserRole.ROLE_INSTRUCTOR
    ).exists()


@pytest.mark.parametrize(
    "title, content, order, should_raise",
    [
        (
            "Lesson 1",
            "Content 1",
            1,
            False,
        ),
        (
            "",
            "Content 1",
            1,
            True,
        ),
        (
            "Lesson 1",
            "",
            1,
            True,
        ),
        (
            "Lesson 1",
            "Content 1",
            None,
            True,
        ),
    ],
)
def test_lesson_validation(course, title, content, order, should_raise):
    """
    Test lesson validation for various title, content, and order combinations.
    """
    lesson = Lesson(
        course=course,
        title=title,
        content=content,
        order=order,
    )
    if should_raise:
        with pytest.raises(ValidationError):
            lesson.full_clean()
    else:
        lesson.full_clean()


@pytest.mark.parametrize(
    "existing_roles, new_role, should_raise",
    [
        (
            [],
            UserRole.ROLE_INSTRUCTOR,
            False,
        ),
        (
            [UserRole.ROLE_INSTRUCTOR],
            UserRole.ROLE_INSTRUCTOR,
            True,
        ),
        (
            [],
            UserRole.ROLE_STUDENT,
            False,
        ),
    ],
)
def test_single_instructor_validation(
    course, user, existing_roles, new_role, should_raise
):
    """
    Test that a course can only have one instructor.
    """
    for role in existing_roles:
        UserRole.objects.create(user=user, course=course, role=role)

    new_user = User.objects.create_user(
        username="new_user", email="new_user@test.com", password="password"
    )
    new_role_instance = UserRole(user=new_user, course=course, role=new_role)

    if should_raise:
        with pytest.raises(
            ValidationError, match="A course can only have one instructor."
        ):
            new_role_instance.full_clean()
    else:
        new_role_instance.full_clean()
        new_role_instance.save()
        assert UserRole.objects.filter(
            user=new_user, course=course, role=new_role
        ).exists()


def test_assign_instructor(user, course):
    """
    Test assigning an instructor role.
    """
    course.assign_instructor(user)
    assert UserRole.objects.filter(
        user=user, course=course, role=UserRole.ROLE_INSTRUCTOR
    ).exists()


def test_enroll_student(user, course):
    """
    Test enrolling a student.
    """
    course.enroll_student(user)
    assert UserRole.objects.filter(
        user=user, course=course, role=UserRole.ROLE_STUDENT
    ).exists()


def test_lesson_ordering(course):
    """
    Test lessons are ordered correctly within a course.
    """
    lesson1 = Lesson.objects.create(
        course=course, title="Lesson 1", content="Content 1", order=2
    )
    lesson2 = Lesson.objects.create(
        course=course, title="Lesson 2", content="Content 2", order=1
    )
    lessons = Lesson.objects.filter(course=course).order_by("order")
    assert lessons[0] == lesson2
    assert lessons[1] == lesson1
