from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from courses.models import Course


class CourseTests(APITestCase):
    PASSWORD = "testpassword"

    def setUp(self):
        self.normal_user = User.objects.create_user(
            username="normal_user", email="normal_user@test.com"
        )
        self.normal_user.set_password(self.PASSWORD)
        self.normal_user.save()

        self.super_user = User.objects.create_user(
            username="super_user", email="super_user@test.com"
        )
        self.super_user.set_password(self.PASSWORD)
        self.super_user.is_superuser = True
        self.super_user.save()

        self.first_course = Course.objects.create(
            title="Test First Course",
            description="First course for testing.",
            instructor=self.normal_user,
        )

        self.second_course = Course.objects.create(
            title="Test Second Course",
            description="Second course for testing.",
            instructor=self.normal_user,
        )

        self.course_list = reverse("course-list")
        self.first_course_detail = reverse(
            "course-detail",
            kwargs={"pk": self.first_course.id},
        )

    def test_list_courses_not_login_user(self):
        response = self.client.get(self.course_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_list_courses_login_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.course_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "Test First Course")
        self.assertEqual(response.data[0]["description"], "First course for testing.")
        self.assertEqual(response.data[0]["instructor"], self.normal_user.id)
        self.assertIsNotNone(response.data[0]["created_at"])
        self.assertIsNotNone(response.data[0]["updated_at"])
        self.assertEqual(response.data[1]["title"], "Test Second Course")
        self.assertEqual(response.data[1]["description"], "Second course for testing.")
        self.assertEqual(response.data[1]["instructor"], self.normal_user.id)
        self.assertIsNotNone(response.data[1]["created_at"])
        self.assertIsNotNone(response.data[1]["updated_at"])

    # def test_student_can_see_published_courses(self):
    #     self.client.force_authenticate(user=self.normal_user)
    #     response = self.client.get(self.course_list)
    #     assert response.status_code == 200
    #     assert len(response.data) == 1

    # def test_student_cannot_see_unpublished_courses(self):
    #     self.client.force_authenticate(user=self.normal_user)
    #     response = self.client.get(self.course_list)
    #     assert response.status_code == 200
    #     assert len(response.data) == 0

    # def test_superuser_can_see_all_courses(self):
    #     self.client.force_authenticate(user=self.super_user)
    #     response = self.client.get(self.course_list)
    #     assert response.status_code == 200
    #     assert len(response.data) == 2

    def test_create_course_not_login_user(self):
        data = {
            "title": "New Course",
            "description": "New course description.",
            "instructor": self.normal_user.id,
        }
        response = self.client.post(self.course_list, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    # test_create_course_student
    # test_create_course_teacher
    def test_create_course_login_normal_user(self):
        data = {
            "title": "New Course",
            "description": "New course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(self.course_list, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["id"], 3)
        self.assertEqual(response.data["title"], "New Course")
        self.assertEqual(response.data["description"], "New course description.")
        self.assertEqual(response.data["instructor"], self.normal_user.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_retrieve_course_not_login_user(self):
        response = self.client.get(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_retrieve_course_login_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data["id"], 10)
        self.assertEqual(response.data["title"], self.first_course.title)
        self.assertEqual(response.data["description"], self.first_course.description)
        self.assertEqual(response.data["instructor"], self.normal_user.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_update_course_not_login_user(self):
        data = {
            "title": "New Course",
            "description": "New course description.",
            "instructor": self.normal_user.id,
        }
        response = self.client.put(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_update_course_login_normal_user(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.put(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Course")
        self.assertEqual(response.data["description"], "Updated Course description.")

    # def test_update_course_login_normal_user_without_instructor(self):
    #     data = {
    #         "title": "Updated Course",
    #         "description": "Updated Course description.",
    #     }
    #     self.client.force_authenticate(user=self.normal_user)
    #     response = self.client.put(self.first_course_detail, data=data)
    #     assert response.data == ""
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data["title"], "Updated Course")
    #     self.assertEqual(response.data["description"], "Updated Course description.")

    def test_partial_update_course_not_login_user(self):
        data = {
            "title": "New Course",
            "description": "New course description.",
            "instructor": self.normal_user.id,
        }
        response = self.client.patch(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_partial_update_course_login_normal_user(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.patch(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Course")
        self.assertEqual(response.data["description"], "Updated Course description.")

    def test_partial_update_course_login_normal_user_without_instructor(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
        }
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.patch(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Course")
        self.assertEqual(response.data["description"], "Updated Course description.")

    def test_delete_course_login_normal_user(self):
        response = self.client.delete(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_delete_course_login_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.delete(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
