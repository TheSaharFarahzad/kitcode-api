from rest_framework import permissions
from courses.models import UserRole


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow instructors to edit or delete a course,
    while others can only view the course.
    """

    def has_permission(self, request, view):
        # Allow read-only (SAFE_METHODS) for all users
        if request.method in permissions.SAFE_METHODS:
            return True

        # For non-read-only methods, user must be authenticated
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission:
        - Allow SAFE_METHODS for all users
        - Allow modifications only if the user is an instructor for the course
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        return UserRole.objects.filter(
            user=request.user, course=obj, role="instructor"
        ).exists()


class IsAuthorizedForLesson(permissions.BasePermission):
    """
    Custom permission to allow only:
    - The instructor of the course to view and manage lessons.
    - Enrolled students to view lessons in the course.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        course_pk = view.kwargs.get("course_pk")
        if not course_pk:
            return False

        # Allow access if the user is the instructor or a student in the course
        return UserRole.objects.filter(
            user=request.user, course_id=course_pk, role__in=["instructor", "student"]
        ).exists()

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission:
        - Only instructors of the course can modify the lessons.
        - Only enrolled students can view lessons in the course.
        """
        if request.method in permissions.SAFE_METHODS:
            # Allow enrolled students or the instructor to view
            return UserRole.objects.filter(
                user=request.user, course=obj.course, role__in=["instructor", "student"]
            ).exists()

        # Allow write permissions only to the instructor of the course
        return UserRole.objects.filter(
            user=request.user, course=obj.course, role="instructor"
        ).exists()
