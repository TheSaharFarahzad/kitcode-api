from django.contrib import admin
from .models import Course, Lesson


class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "created_at", "updated_at")
    search_fields = ("title", "instructor__username")


class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    search_fields = ("title", "course__title")
    list_filter = ("course",)


admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
