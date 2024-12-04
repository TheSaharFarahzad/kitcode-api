from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q

from .models import Course, Lesson, UserRole
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsInstructorOrReadOnly, IsAuthorizedForLesson


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing courses:
    - Instructors can create, update, or delete courses.
    - Authenticated users can enroll in courses.
    - All users can view published courses.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsInstructorOrReadOnly]

    def get_queryset(self):
        """
        Retrieve courses based on the user's role:
        - Authenticated users: Courses they created or published courses.
        - Unauthenticated users: Published courses only.
        """
        user = self.request.user
        if user.is_authenticated:
            return Course.objects.filter(
                Q(is_published=True) | Q(created_by=user)
            ).distinct()
        return Course.objects.filter(is_published=True)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        """
        Enroll the requesting user as a student in the specified course.
        """
        course = self.get_object()
        course.enroll_student(request.user)
        return Response({"status": "enrolled"})


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing lessons:
    - Instructors can create, update, or delete lessons.
    - Students can view lessons from published courses.
    """

    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsAuthorizedForLesson]

    def get_queryset(self):
        """
        Retrieve lessons for the specified course based on the user's role:
        - Instructors: All lessons.
        - Students: Lessons in published courses only.
        """
        course_pk = self.kwargs.get("course_pk")
        if not course_pk:
            return Lesson.objects.none()

        course = Course.objects.filter(pk=course_pk).first()
        if not course:
            return Lesson.objects.none()

        if UserRole.objects.is_role(
            self.request.user, course, UserRole.ROLE_INSTRUCTOR
        ):
            return Lesson.objects.filter(course=course)
        elif UserRole.objects.is_role(self.request.user, course, UserRole.ROLE_STUDENT):
            return Lesson.objects.filter(course=course, course__is_published=True)
        return Lesson.objects.none()

    def perform_create(self, serializer):
        """
        Create a new lesson in the specified course.
        - Only instructors can create lessons.
        """
        course_pk = self.kwargs.get("course_pk")
        course = Course.objects.get(pk=course_pk)

        if not UserRole.objects.is_role(
            self.request.user, course, UserRole.ROLE_INSTRUCTOR
        ):
            raise PermissionDenied("Only instructors can create lessons.")

        serializer.save(course=course)
