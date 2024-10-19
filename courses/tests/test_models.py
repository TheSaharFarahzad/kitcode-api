from django.test import TestCase
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson
from django.core.exceptions import ValidationError

User = get_user_model()


class CourseLessonTestCase(TestCase):
    PASSWORD = "testpassword"

    def setUp(self):
        self.normal_user = User.objects.create_user(
            username="normal_user", email="normal_user@test.com"
        )
        self.normal_user.set_password(self.PASSWORD)
        self.normal_user.save()

        self.course = Course.objects.create(
            title="Django Web Development",
            description="Learn Django from scratch.",
            instructor=self.normal_user,
        )

        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Introduction to Django",
            content="This is the first lesson.",
            order=1,
        )

    def test_course_creation(self):
        self.assertEqual(self.course.title, "Django Web Development")
        self.assertEqual(self.course.description, "Learn Django from scratch.")
        self.assertEqual(self.course.instructor, self.normal_user)
        self.assertIsNotNone(self.course.created_at)
        self.assertIsNotNone(self.course.updated_at)

    def test_lesson_creation(self):
        self.assertEqual(self.lesson.title, "Introduction to Django")
        self.assertEqual(self.lesson.content, "This is the first lesson.")
        self.assertEqual(self.lesson.course, self.course)
        self.assertEqual(self.lesson.order, 1)

    def test_course_without_title_raises_error(self):
        course = Course(
            title="",
            description="No title course.",
            instructor=self.normal_user,
        )
        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_course_without_description_raises_error(self):
        course = Course(
            title="Valid Title",
            description="",
            instructor=self.normal_user,
        )
        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_course_without_instructor_raises_error(self):
        course = Course(
            title="Valid Title",
            description="Course description.",
            instructor=None,
        )
        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_lesson_without_title_raises_error(self):
        lesson = Lesson(
            course=self.course,
            title="",
            content="Content of the lesson.",
            order=1,
        )
        with self.assertRaises(ValidationError):
            lesson.full_clean()

    def test_lesson_without_content_raises_error(self):
        lesson = Lesson(
            course=self.course,
            title="Lesson Title",
            content="",
            order=1,
        )
        with self.assertRaises(ValidationError):
            lesson.full_clean()

    def test_lesson_without_order_raises_error(self):
        lesson = Lesson(
            course=self.course,
            title="Lesson without order",
            content="Content without order.",
        )
        with self.assertRaises(ValidationError):
            lesson.full_clean()

    def test_lesson_order_validation(self):
        lesson1 = Lesson.objects.create(
            course=self.course,
            title="Lesson 1",
            content="Content of lesson 1",
            order=1,
        )

        lesson2 = Lesson.objects.create(
            course=self.course,
            title="Lesson 2",
            content="Content of lesson 2",
            order=2,
        )

        self.assertLess(lesson1.order, lesson2.order)

    def test_lesson_without_course_raises_error(self):
        lesson = Lesson(
            title="Lesson without course",
            content="Content of lesson without course.",
            order=1,
        )
        with self.assertRaises(ValidationError):
            lesson.full_clean()
