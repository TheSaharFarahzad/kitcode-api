from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from dj_rest_auth.serializers import PasswordResetSerializer
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from PIL import Image

User = get_user_model()


class CustomPasswordResetSerializer(PasswordResetSerializer):
    """
    Custom serializer for password reset with additional email validation.
    """

    def validate_email(self, value):
        """
        Validates the provided email for password reset.
        """
        # Initialize the reset form and validate it
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise ValidationError(self.reset_form.errors)

        # Check if the email exists and is linked to an active user
        user = User.objects.filter(email=value).first()
        if not user:
            raise ValidationError(
                {"email": "This email address is not associated with any account."}
            )

        if not user.is_active:
            raise ValidationError(
                {"email": "This account is inactive. Please contact support."}
            )

        return value


class CustomResendEmailVerificationSerializer(serializers.Serializer):
    """
    Serializer to handle email verification resend requests.
    """

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Validates the email for existence in the EmailAddress model.
        """
        if not EmailAddress.objects.filter(email=value).exists():
            raise ValidationError("Email address not found.")
        return value


class CustomUserDetailsSerializer(serializers.ModelSerializer):
    picture = serializers.ImageField(required=False)
    username = serializers.CharField(required=False, allow_blank=False)
    email = serializers.EmailField(required=False, allow_blank=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "picture",
        ]
        read_only_fields = ["id"]

    def validate_picture(self, value):
        """
        Ensure that the uploaded file is a valid image and matches allowed formats.
        """
        print(f"Validating picture: {value}")
        if value:
            if value.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
                raise serializers.ValidationError(
                    "Upload a valid image. The file you uploaded was either not an image or a corrupted image."
                )
            try:
                # Validate the image content
                Image.open(value).verify()
            except (DjangoValidationError, IOError):
                raise serializers.ValidationError(
                    "Upload a valid image. The file you uploaded was either not an image or a corrupted image."
                )
        return value

    def validate_username(self, value):
        """
        Ensure the username is valid and unique, but not for the current user.
        """
        if not value:
            raise serializers.ValidationError(_("This field may not be blank."))

        user = self.context.get("request").user

        # If username is being updated to the same as current, don't check for uniqueness
        if value == user.username:
            return value

        # Check if the new username already exists in other users
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("This username is already taken"))

        return value

    def validate_email(self, value):
        """
        Ensure the email is not empty and follows validation logic, but not for the current user.
        """
        if not value:  # Check if email is empty
            raise serializers.ValidationError(_("This field may not be blank."))

        # Get the current user from the context (assumes the view is passing it)
        user = self.context.get("request").user

        # If email is being updated to the same as current, don't check for uniqueness
        if value == user.email:
            return value

        # Check if the new email already exists in other users
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("This email is already registered"))

        return value
