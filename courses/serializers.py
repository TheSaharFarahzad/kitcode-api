from rest_framework import serializers
from .models import Course, Lesson


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for the Course model.
    - Excludes `created_by` from user input, automatically assigning it to the request user.
    """

    class Meta:
        model = Course
        exclude = ["created_by"]

    def create(self, validated_data):
        """
        Create a new course, assigning the request user as its creator and instructor.
        """
        user = self.context["request"].user
        validated_data.pop("created_by", None)
        course = Course.objects.create(created_by=user, **validated_data)
        course.assign_instructor(user)
        return course


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for the Lesson model.
    - Ensures lesson order is unique within a course.
    """

    class Meta:
        model = Lesson
        fields = "__all__"

    def validate(self, attrs):
        """
        Validate lesson order to ensure uniqueness within the course.
        """
        course = attrs.get("course")
        if Lesson.objects.filter(course=course, order=attrs["order"]).exists():
            raise serializers.ValidationError(
                "Lesson order must be unique within the course."
            )
        return attrs
