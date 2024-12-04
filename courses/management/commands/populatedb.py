import random
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from courses.models import Course, UserRole, Lesson
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = "Populate the database with test data for users, courses, and lessons."

    def handle(self, *args, **kwargs):
        # Flush the database to ensure a clean slate
        self.stdout.write(self.style.NOTICE("Flushing the database..."))
        from django.core.management import call_command

        call_command("flush", "--no-input")

        # Apply migrations (in case some are pending)
        self.stdout.write(self.style.NOTICE("Applying migrations..."))
        call_command("migrate")

        # Create users with different roles
        self.stdout.write(self.style.NOTICE("Creating users..."))

        # Create the superuser (admin user)
        admin_user = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="1234.qaz",  # Updated password
        )
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.bio = "I am the admin user with full privileges."
        admin_user.picture = "admin_profile_pic.jpg"
        admin_user.save()

        # Create other users with different roles
        student_user = get_user_model().objects.create_user(
            username="student_user",
            email="student@example.com",
            password="1234.qaz",  # Updated password
        )
        student_user.bio = "I am a student enrolled in courses."
        student_user.picture = "student_profile_pic.jpg"
        student_user.save()

        instructor_user = get_user_model().objects.create_user(
            username="instructor_user",
            email="instructor@example.com",
            password="1234.qaz",  # Updated password
        )
        instructor_user.bio = "I am an instructor teaching courses."
        instructor_user.picture = "instructor_profile_pic.jpg"
        instructor_user.save()

        regular_user = get_user_model().objects.create_user(
            username="regular_user",
            email="regular@example.com",
            password="1234.qaz",  # Updated password
        )
        regular_user.bio = "I am a regular user with no special roles."
        regular_user.picture = "regular_profile_pic.jpg"
        regular_user.save()

        # Create a user who has both roles (student and instructor)
        both_user = get_user_model().objects.create_user(
            username="both_user",
            email="both@example.com",
            password="1234.qaz",  # Updated password
        )
        both_user.bio = "I am both a student and an instructor."
        both_user.picture = "both_profile_pic.jpg"
        both_user.save()

        self.stdout.write(self.style.SUCCESS("Users created successfully."))

        # Manually mark emails as verified
        self._mark_email_verified(admin_user)
        self._mark_email_verified(student_user)
        self._mark_email_verified(instructor_user)
        self._mark_email_verified(regular_user)
        self._mark_email_verified(both_user)

        # Create courses
        self.stdout.write(self.style.NOTICE("Creating courses..."))

        course1 = Course.objects.create(
            title="Course 1",
            description="Introduction to Django.",
            created_by=instructor_user,
        )
        course2 = Course.objects.create(
            title="Course 2", description="Advanced Django.", created_by=instructor_user
        )

        course3 = Course.objects.create(
            title="Course 3",
            description="Basic Python Programming.",
            created_by=instructor_user,
        )

        # Publish courses
        course1.publish()
        course2.publish()
        course3.publish()

        self.stdout.write(
            self.style.SUCCESS("Courses created and published successfully.")
        )

        # Assign roles to users in courses
        self.stdout.write(self.style.NOTICE("Assigning roles to users in courses..."))

        # Admin user - no roles (can be added manually later)
        # Student user - enrolled in Course 1 and Course 2
        self.create_user_role(student_user, course1, "student")
        self.create_user_role(student_user, course2, "student")

        # Instructor user - teaching Course 1 and Course 2
        self.create_user_role(instructor_user, course1, "instructor")
        self.create_user_role(instructor_user, course2, "instructor")

        # Regular user - enrolled in Course 3 (student role)
        self.create_user_role(regular_user, course3, "student")

        # Both user - enrolled in Course 1 (student role) and Course 2 (instructor role)
        self.create_user_role(both_user, course1, "student")
        self.create_user_role(both_user, course2, "instructor")

        self.stdout.write(self.style.SUCCESS("Roles assigned successfully."))

        # Create lessons for each course
        self.stdout.write(self.style.NOTICE("Creating lessons for courses..."))

        Lesson.objects.create(
            course=course1, title="Lesson 1", content="Django Introduction", order=1
        )
        Lesson.objects.create(
            course=course1, title="Lesson 2", content="Setting up Django", order=2
        )

        Lesson.objects.create(
            course=course2, title="Lesson 1", content="Advanced Django Topics", order=1
        )
        Lesson.objects.create(
            course=course2, title="Lesson 2", content="Django with React", order=2
        )

        Lesson.objects.create(
            course=course3, title="Lesson 1", content="Python Basics", order=1
        )
        Lesson.objects.create(
            course=course3,
            title="Lesson 2",
            content="Python for Web Development",
            order=2,
        )

        self.stdout.write(self.style.SUCCESS("Lessons created successfully."))

        self.stdout.write(self.style.SUCCESS("Database populated successfully!"))

    def create_user_role(self, user, course, role):
        """Helper function to avoid duplicate roles."""
        if not UserRole.objects.filter(user=user, course=course, role=role).exists():
            UserRole.objects.create(user=user, course=course, role=role)

    def _mark_email_verified(self, user):
        """Helper function to mark the user's email as verified."""
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )
