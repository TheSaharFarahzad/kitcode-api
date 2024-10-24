from rest_framework import serializers
from .models import Course, Lesson
from users.models import User


class CourseSerializer(serializers.ModelSerializer):
    instructor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "instructor",
        ]


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "title",
            "content",
            "order",
        ]

    def validate_order(self, value):
        # Check if a lesson with the same order exists for the given course
        course = self.initial_data.get("course")
        if Lesson.objects.filter(order=value, course=course).exists():
            raise serializers.ValidationError("This order exists.")
        return value
