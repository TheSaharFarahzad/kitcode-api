from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from django.utils.translation import gettext_lazy as _
from courses.models import UserRole, Course


class CustomUserAdmin(UserAdmin):
    # Specify the fields to display in the admin list view
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "bio",
        "date_joined",
        "is_active",
    )
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    # Specify the fields for the user detail page
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "bio", "picture")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "email",
                    "bio",
                    "picture",
                ),
            },
        ),
    )

    # Custom method to display roles in courses
    def roles_in_courses(self, obj):
        # Get all the roles for the user
        user_roles = UserRole.objects.filter(user=obj)
        # If user has roles in courses, display them
        if user_roles:
            course_roles = [f"{role.course.title} - {role.role}" for role in user_roles]
            return ", ".join(course_roles)
        return "No roles"

    roles_in_courses.short_description = "Roles in Courses"

    # Add the custom field to the user list page
    list_display += ("roles_in_courses",)


# Register the custom user admin interface
admin.site.register(User, CustomUserAdmin)
