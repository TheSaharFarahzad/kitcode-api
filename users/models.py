from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model for the platform.
    Users are authenticated but have no predefined role until assigned dynamically
    based on course actions.
    """

    bio = models.TextField(
        blank=True, help_text="A short description or biography of the user."
    )
    picture = models.ImageField(
        default="default_profile_pic.jpg",
        upload_to="profile_pics",
        blank=True,
        help_text="Profile picture of the user.",
    )

    class Meta:
        ordering = ("-date_joined",)

    def __str__(self):
        return self.username

    def roles_in_course(self, course):
        """
        Retrieve all roles for the user in a specific course.
        Returns a flat list of role names.
        """
        return self.roles.filter(course=course).values_list("role", flat=True)

    def is_student_in_course(self, course):
        """
        Check if the user is a student in the specified course.
        """
        return self.roles.filter(course=course, role="student").exists()

    def is_instructor_in_course(self, course):
        """
        Check if the user is an instructor in the specified course.
        """
        return self.roles.filter(course=course, role="instructor").exists()
