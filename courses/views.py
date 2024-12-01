from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Course, Lesson, UserRole
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import (
    IsInstructorOrReadOnly,
    IsAuthorizedForLesson,
)
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsInstructorOrReadOnly]

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        """
        Enroll the authenticated user as a student in the course.
        """
        course = self.get_object()
        course.enroll_student(request.user)
        return Response({"status": "enrolled"})

    def get_queryset(self):
        """
        Limit the courses returned based on user role.
        """
        user = self.request.user
        if user.is_authenticated:
            # Show courses the user created or all published courses
            return Course.objects.filter(
                Q(is_published=True) | Q(created_by=user)
            ).distinct()
        # For unauthenticated users, show only published courses
        return Course.objects.filter(is_published=True)


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsAuthorizedForLesson]

    def get_queryset(self):
        """
        Restrict the lessons visible to the current user:
        - Instructors: All lessons for their course.
        - Students: Lessons only from their enrolled courses.
        """
        course_pk = self.kwargs["course_pk"]
        course = Course.objects.get(pk=course_pk)

        if not UserRole.objects.filter(
            user=self.request.user, course=course, role__in=["instructor", "student"]
        ).exists():
            # Return no lessons for unauthorized users
            return Lesson.objects.none()

        if UserRole.objects.filter(
            user=self.request.user, course=course, role="instructor"
        ).exists():
            # Instructor can view all lessons in their course
            return Lesson.objects.filter(course=course)

        if UserRole.objects.filter(
            user=self.request.user, course=course, role="student"
        ).exists():
            # Students can only view lessons in their enrolled courses
            return Lesson.objects.filter(course=course, course__is_published=True)

        return Lesson.objects.none()

    def perform_create(self, serializer):
        """
        Ensure only the instructor of the course can create lessons.
        """
        course = Course.objects.get(pk=self.kwargs["course_pk"])
        if not UserRole.objects.filter(
            user=self.request.user, course=course, role="instructor"
        ).exists():
            raise PermissionDenied(
                "Only the instructor of the course can create lessons."
            )
        serializer.save(course=course)
