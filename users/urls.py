from django.urls import path
from users.views import UserDetailsView

urlpatterns = [
    path("user/", UserDetailsView.as_view(), name="rest_user_details"),
]
