from dj_rest_auth.registration.views import ResendEmailVerificationView
from dj_rest_auth.views import LoginView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveUpdateAPIView
from django.contrib.auth import get_user_model
from .serializers import CustomResendEmailVerificationSerializer, UserSerializer


User = get_user_model()


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


class UserDetailsView(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
