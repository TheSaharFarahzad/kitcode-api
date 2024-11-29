from django.contrib import admin
from django.db import models  # Import the models module
from .models import Course, UserRole, Lesson


class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "is_published", "created_at", "updated_at")
    list_filter = ("is_published", "created_by")
    search_fields = ("title", "description")
    ordering = ("-created_at",)
    actions = ["publish_courses"]

    def publish_courses(self, request, queryset):
        """
        Action to mark selected courses as published.
        """
        for course in queryset:
            if not course.is_published:
                course.publish()
        self.message_user(request, "Selected courses have been published.")

    publish_courses.short_description = "Mark selected courses as published"


class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "role", "date_assigned")
    list_filter = ("role", "course", "user")
    search_fields = ("user__username", "course__title", "role")

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of UserRole if the user is an instructor.
        if obj and obj.role == "instructor":
            return False
        return super().has_delete_permission(request, obj)


class LessonAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "order", "content")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    ordering = ("course", "order")

    def save_model(self, request, obj, form, change):
        """
        Ensure that lessons have a unique order number within the course.
        """
        if not change:  # If it's a new object.
            max_order = Lesson.objects.filter(course=obj.course).aggregate(
                models.Max("order")
            )["order__max"]
            obj.order = (max_order or 0) + 1
        super().save_model(request, obj, form, change)


# Register models with the admin interface
admin.site.register(Course, CourseAdmin)
admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(Lesson, LessonAdmin)
