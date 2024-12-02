from rest_framework import permissions
from courses.models import UserRole


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Allows instructors to modify a course.
    - Grants read-only access (SAFE_METHODS) to all users.
    """

    def has_permission(self, request, view) -> bool:
        """
        Global permission check.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj) -> bool:
        """
        Object-level permission:
        - Read-only access for all users.
        - Write access only for instructors of the course.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        return UserRole.objects.is_role(
            user=request.user, course=obj, role=UserRole.ROLE_INSTRUCTOR
        )


class IsAuthorizedForLesson(permissions.BasePermission):
    """
    Custom permission:
    - Grants access to lessons if the user is enrolled in the course
      (as an instructor or a student).
    - Write access is restricted to instructors only.
    """

    def has_permission(self, request, view) -> bool:
        """
        Global permission check for lessons.
        """
        if not request.user.is_authenticated:
            return False

        course_pk = view.kwargs.get("course_pk")
        if not course_pk:
            return False

        return UserRole.objects.filter(
            user=request.user,
            course_id=course_pk,
            role__in=[UserRole.ROLE_INSTRUCTOR, UserRole.ROLE_STUDENT],
        ).exists()

    def has_object_permission(self, request, view, obj) -> bool:
        """
        Object-level permission for lessons.
        - Read-only access for enrolled users.
        - Write access for instructors only.
        """
        if request.method in permissions.SAFE_METHODS:
            return UserRole.objects.filter(
                user=request.user,
                course=obj.course,
                role__in=[UserRole.ROLE_INSTRUCTOR, UserRole.ROLE_STUDENT],
            ).exists()

        return UserRole.objects.is_role(
            user=request.user, course=obj.course, role=UserRole.ROLE_INSTRUCTOR
        )
