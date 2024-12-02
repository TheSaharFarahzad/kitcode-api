from django.contrib import admin
from django.db import models, transaction
from .models import Course, UserRole, Lesson


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("title", "order")
    ordering = ("order",)


class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "is_published", "created_at", "updated_at")
    list_filter = ("is_published", "created_by")
    search_fields = ("title", "description")
    ordering = ("-created_at",)
    actions = ["publish_courses"]
    inlines = [LessonInline]

    @transaction.atomic
    def publish_courses(self, request, queryset):
        for course in queryset:
            if not course.is_published:
                course.publish()
        self.message_user(request, f"{queryset.count()} courses have been published.")

    publish_courses.short_description = "Mark selected courses as published"


class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "role", "date_assigned")
    list_filter = ("role", "course", "user")
    search_fields = ("user__username", "course__title", "role")

    def has_delete_permission(self, request, obj=None):
        if obj and obj.role == UserRole.ROLE_INSTRUCTOR:
            self.message_user(
                request, "Instructor roles cannot be deleted.", level="error"
            )
            return False
        return super().has_delete_permission(request, obj)

    @admin.action(description="Assign 'Student' role to selected users")
    def assign_student_role(self, request, queryset):
        for user_role in queryset:
            user_role.role = UserRole.ROLE_STUDENT
            user_role.save()
        self.message_user(
            request, "Selected users have been assigned the 'Student' role."
        )


class LessonAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "order", "content")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    ordering = ("course", "order")

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if not change:
            max_order = Lesson.objects.filter(course=obj.course).aggregate(
                models.Max("order")
            )["order__max"]
            obj.order = (max_order or 0) + 1
        else:
            existing = Lesson.objects.filter(course=obj.course, order=obj.order)
            if existing.exists() and existing.first().id != obj.id:
                self.message_user(
                    request,
                    "A lesson with this order already exists in the course.",
                    level="error",
                )
                return
        super().save_model(request, obj, form, change)


admin.site.register(Course, CourseAdmin)
admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(Lesson, LessonAdmin)
