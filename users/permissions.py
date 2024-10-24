from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsInstructorOrReadOnly(BasePermission):
    """
    Custom permission to allow instructors to perform all operations,
    and all users to have read-only access.
    """

    def has_permission(self, request, view):
        # Allow all users to perform SAFE_METHODS
        if request.method in SAFE_METHODS:
            return True

        # Allow only authenticated instructors to perform non-safe methods
        return request.user.is_authenticated and request.user.is_instructor

    def has_object_permission(self, request, view, obj):
        # Allow all users to perform SAFE_METHODS on any object
        if request.method in SAFE_METHODS:
            return True

        # Allow instructors to perform all operations on the course they created
        return request.user == obj.instructor


class IsInstructor(BasePermission):
    """
    Custom permission to allow only instructors to create/update/delete lessons.
    """

    def has_permission(self, request, view):
        # Allow only authenticated instructors for safe methods
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        # Allow only authenticated instructors to perform CRUD operations
        return request.user.is_authenticated and request.user.is_instructor

    def has_object_permission(self, request, view, obj):
        # Allow CRUD if the user is the instructor of the lesson's course
        if request.user == obj.course.instructor:
            return True

        # Otherwise, allow only safe methods
        return request.method in SAFE_METHODS


class IsStudent(BasePermission):
    """
    Custom permission to allow only students to view lessons (GET).
    """

    def has_permission(self, request, view):
        user = request.user
        # Allow students to view lessons (GET) only
        return (
            user.is_authenticated and user.is_student and request.method in SAFE_METHODS
        )


class IsAuthenticatedUser(BasePermission):
    """
    Custom permission to allow only authenticated users (not student or instructor).
    """

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated
            and not user.is_student
            and not user.is_instructor
            and request.method in SAFE_METHODS
        )
