from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Course(models.Model):
    """
    Represents a course in the platform.
    A course can have lessons and assigned roles (instructor, students).
    """

    title = models.CharField(max_length=255, help_text="Title of the course.")
    description = models.TextField(help_text="Detailed description of the course.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_courses",
        help_text="The user who created this course.",
    )
    is_published = models.BooleanField(
        default=False, help_text="Indicates whether the course is published."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the course was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Timestamp when the course was last updated."
    )

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def publish(self):
        """
        Publishes the course and assigns the creator as the instructor.
        """
        self.is_published = True
        self.save()
        self.assign_instructor(self.created_by)

    def assign_instructor(self, user):
        """
        Assigns the 'instructor' role to the user for this course.
        """
        UserRole.objects.get_or_create(
            user=user, course=self, role=UserRole.ROLE_INSTRUCTOR
        )

    def enroll_student(self, user):
        """
        Enrolls the user as a 'student' in this course.
        """
        UserRole.objects.get_or_create(
            user=user, course=self, role=UserRole.ROLE_STUDENT
        )


class RoleManager(models.Manager):
    """
    Manager for the UserRole model, providing additional query utilities.
    """

    def for_user_and_course(self, user, course):
        """
        Fetches roles for a specific user in a specific course.
        """
        return self.filter(user=user, course=course)

    def is_role(self, user, course, role):
        """
        Checks if the user has the specified role in the course.
        """
        return self.for_user_and_course(user, course).filter(role=role).exists()


class UserRole(models.Model):
    """
    Represents a user's role in a specific course (e.g., instructor, student).
    """

    ROLE_STUDENT = "student"
    ROLE_INSTRUCTOR = "instructor"

    ROLE_CHOICES = [
        (ROLE_STUDENT, "Student"),
        (ROLE_INSTRUCTOR, "Instructor"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roles",
        help_text="The user assigned a role.",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="roles",
        help_text="The course for which the role is assigned.",
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, help_text="Role of the user in the course."
    )
    date_assigned = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the role was assigned."
    )

    objects = RoleManager()

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        unique_together = ("user", "course", "role")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["course"]),
        ]

    def clean(self):
        """
        Validates the role assignment.
        Ensures only one instructor per course.
        """
        if self.role == self.ROLE_INSTRUCTOR and UserRole.objects.is_role(
            None, self.course, self.ROLE_INSTRUCTOR
        ):
            raise ValidationError("A course can only have one instructor.")

    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.course.title}"


class Lesson(models.Model):
    """
    Represents a lesson in a course.
    Each lesson is ordered and associated with a course.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        help_text="The course to which the lesson belongs.",
    )
    title = models.CharField(max_length=255, help_text="Title of the lesson.")
    content = models.TextField(help_text="Content of the lesson.")
    order = models.PositiveIntegerField(
        help_text="Order of the lesson within the course."
    )

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ["order"]
        unique_together = ("course", "order")

    def __str__(self):
        return f"{self.order}. {self.title}"
