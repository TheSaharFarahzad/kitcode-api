from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    https://simpleisbetterthancomplex.com/tutorial/2018/01/18/how-to-implement-multiple-user-types-with-django.html
    """

    is_student = models.BooleanField("student status", default=False)
    is_instructor = models.BooleanField("instructor status", default=False)
