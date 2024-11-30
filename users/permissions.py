from rest_framework import permissions
from courses.models import Course, UserRole


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


class IsEnrolledStudent(permissions.BasePermission):
    """
    Custom permission to check if the user is enrolled as a student in the course.
    """

    def has_permission(self, request, view):
        # Allow anonymous users to see published lessons, if they're not authenticated
        if not request.user.is_authenticated:
            return False

        course_pk = view.kwargs.get("course_pk")  # Get course PK from URL
        if not course_pk:
            return False

        # Ensure the user is enrolled in the course
        return UserRole.objects.filter(
            user=request.user, course_id=course_pk, role="student"
        ).exists()

    def has_object_permission(self, request, view, obj):
        # Check that the user is enrolled in the course for each individual lesson object
        return obj.course.is_published and (
            obj.course.created_by == request.user
            or UserRole.objects.filter(
                user=request.user, course=obj.course, role="student"
            ).exists()
        )


class IsAnonymousOrAuthenticated(permissions.BasePermission):
    """
    Custom permission to allow anonymous users to view courses,
    but only authenticated users can create courses.
    """

    def has_permission(self, request, view):
        # Allow any user to view courses
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow only authenticated users to create courses
        return request.user and request.user.is_authenticated
