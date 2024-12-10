from dj_rest_auth.registration.views import ResendEmailVerificationView
from dj_rest_auth.views import LoginView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import CustomResendEmailVerificationSerializer


User = get_user_model()


class CustomResendEmailVerificationView(ResendEmailVerificationView):
    serializer_class = CustomResendEmailVerificationSerializer


class CustomLoginView(LoginView):
    def get_response(self):
        # Get the default response from the parent class
        response = super().get_response()

        # Generate Simple JWT tokens
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Add the JWT tokens to the response
        response.data["access"] = access_token
        response.data["refresh"] = refresh_token

        # Add the user data to the response
        user_data = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
        }

        response.data["user"] = user_data

        return response
