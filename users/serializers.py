from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from dj_rest_auth.serializers import PasswordResetSerializer

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
