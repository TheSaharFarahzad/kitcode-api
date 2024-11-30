from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Course, Lesson, UserRole
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import (
    IsInstructorOrReadOnly,
    IsEnrolledStudent,
    IsAnonymousOrAuthenticated,
)
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response


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
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsEnrolledStudent, IsInstructorOrReadOnly]

    def get_queryset(self):
        """
        Return lessons for a specific course.
        """
        course_pk = self.kwargs["course_pk"]
        return Lesson.objects.filter(course_id=course_pk)

    def perform_create(self, serializer):
        course = Course.objects.get(pk=self.kwargs["course_pk"])
        serializer.save(course=course)
