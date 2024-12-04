from dj_rest_auth.registration.views import ResendEmailVerificationView
from dj_rest_auth.views import LoginView
from .serializers import CustomResendEmailVerificationSerializer


class CustomResendEmailVerificationView(ResendEmailVerificationView):
    serializer_class = CustomResendEmailVerificationSerializer


class CustomLoginView(LoginView):
    def get_response(self):
        # Get the default response from the parent class
        response = super().get_response()

        # Add the user data to the response
        user_data = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            # Add any other fields you need here
        }

        response.data["user"] = user_data  # Add user data to the response

        return response
