from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = (
        "username",
        "email",
        "is_student",
        "is_instructor",
        "is_active",
        "is_staff",
        "last_login",
    )
    list_filter = ("is_student", "is_instructor", "is_active", "is_staff")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
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
        ("User type", {"fields": ("is_student", "is_instructor")}),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "is_student",
                    "is_instructor",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)


# Register the User model with the custom UserAdmin
admin.site.register(User, UserAdmin)
