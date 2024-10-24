from rest_framework import viewsets
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import (
    IsInstructorOrReadOnly,
    IsInstructor,
    IsStudent,
    IsAuthenticatedUser,
)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsInstructorOrReadOnly]

    def get_queryset(self):
        return self.queryset


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticatedUser | IsStudent | IsInstructor]

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            # If the user is a student, return only the lessons from courses they are enrolled in
            if user.is_student:
                return self.queryset.filter(course__students=user)
            # If the user is an instructor, return lessons from courses they are teaching or enrolled in
            elif user.is_instructor:
                return self.queryset.filter(
                    course__instructor=user
                ) | self.queryset.filter(course__students=user)
            else:
                # For normal users (not students or instructors), return an empty queryset
                return Lesson.objects.none()

        return Lesson.objects.none()  # If the user is not authenticated
