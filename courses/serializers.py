from rest_framework import serializers
from .models import Course, Lesson, UserRole
from users.models import User


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        exclude = ["created_by"]  # Exclude `created_by` from API payload

    def create(self, validated_data):
        """
        Create the course and set the creator explicitly.
        """
        request = self.context.get("request")  # Get request from context
        user = request.user if request and request.user.is_authenticated else None
        # Remove any potential `created_by` key from `validated_data`
        validated_data.pop("created_by", None)
        course = Course.objects.create(created_by=user, **validated_data)
        course.assign_instructor(user)
        return course


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"

    def validate(self, attrs):
        # Ensure the lesson order is unique per course
        if Lesson.objects.filter(course=attrs["course"], order=attrs["order"]).exists():
            raise serializers.ValidationError("Lesson order must be unique per course.")
        return attrs

    # def validate_order(self, value):
    #     # Check if a lesson with the same order exists for the given course
    #     course = self.initial_data.get("course")
    #     if Lesson.objects.filter(order=value, course=course).exists():
    #         raise serializers.ValidationError("This order exists.")
    #     return value
