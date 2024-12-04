from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, LessonViewSet

# Create a DefaultRouter instance and register the viewsets
router = DefaultRouter()
router.register(r"courses", CourseViewSet)
router.register(
    r"courses/(?P<course_pk>\d+)/lessons", LessonViewSet, basename="course-lessons"
)

# Define the URL patterns for the API
urlpatterns = [
    path("api/", include(router.urls)),
]
