from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Course(models.Model):
    """
    Represents a course in the platform.
    Users can enroll as students or create courses as instructors.
    """

    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_courses",
        help_text="The user who created this course.",
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def publish(self):
        """
        Mark the course as published and assign the creator the 'instructor' role.
        """
        self.is_published = True
        self.save()
        # Assign the creator the 'instructor' role in this course.
        UserRole.objects.get_or_create(
            user=self.created_by,
            course=self,
            role="instructor",
        )

    def save(self, *args, **kwargs):
        # Check if the course is being published (is_published=True)
        if self.is_published:
            # Assign the creator as an instructor if not already assigned
            UserRole.objects.get_or_create(
                user=self.created_by,
                course=self,
                role="instructor",
            )

        # # If the course is unpublished, remove the instructor role
        # elif not self.is_published:
        #     # Find and delete the "instructor" role
        #     UserRole.objects.filter(
        #         course=self, user=self.created_by, role="instructor"
        #     ).delete()

        # Call the parent save method to save the course
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class UserRole(models.Model):
    """
    Represents the role of a user within a specific course.
    Roles are assigned dynamically based on actions (enrollment or course creation).
    """

    ROLE_CHOICES = [
        ("student", "Student"),
        ("instructor", "Instructor"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roles"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="roles")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    date_assigned = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course", "role")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["course"]),
        ]

    def clean(self):
        """
        Validate role constraints.
        Example: Only one instructor can be assigned per course.
        """
        if (
            self.role == "instructor"
            and UserRole.objects.filter(course=self.course, role="instructor").exists()
        ):
            raise ValidationError("A course can only have one instructor.")

    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.course.title}"


class Lesson(models.Model):
    """
    Represents a lesson in a course.
    Lessons are ordered within their course.
    """

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        unique_together = ("course", "order")

    def __str__(self):
        return f"{self.order}. {self.title}"
