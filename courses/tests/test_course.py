from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User
from courses.models import Course


class CourseTests(APITestCase):
    PASSWORD = "testpassword"

    @classmethod
    def setUpTestData(self):
        self.normal_user = User.objects.create_user(
            username="normal_user", email="normal_user@test.com"
        )
        self.normal_user.set_password(self.PASSWORD)
        self.normal_user.save()

        self.student = User.objects.create_user(
            username="student", email="student@test.com"
        )
        self.student.set_password(self.PASSWORD)
        self.student.is_student = True
        self.student.save()

        self.instructor = User.objects.create_user(
            username="instructor", email="instructor@test.com"
        )
        self.instructor.set_password(self.PASSWORD)
        self.instructor.is_instructor = True
        self.instructor.save()

        self.instructor_of_lesson = User.objects.create_user(
            username="The Instructor", email="theinstructor@test.com"
        )
        self.instructor_of_lesson.set_password(self.PASSWORD)
        self.instructor_of_lesson.is_instructor = True
        self.instructor_of_lesson.save()

        self.super_user = User.objects.create_user(
            username="super_user", email="super_user@test.com"
        )
        self.super_user.set_password(self.PASSWORD)
        self.super_user.is_superuser = True
        self.super_user.save()

        self.first_course = Course.objects.create(
            title="Test First Course",
            description="First course for testing.",
            instructor=self.instructor_of_lesson,
        )
        self.first_course.students.set([self.student])

        self.second_course = Course.objects.create(
            title="Test Second Course",
            description="Second course for testing.",
            instructor=self.instructor,
        )

        self.course_list = reverse("course-list")
        self.first_course_detail = reverse(
            "course-detail",
            kwargs={"pk": self.first_course.id},
        )

    def test_list_courses_not_login_user(self):
        response = self.client.get(self.course_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "Test First Course")
        self.assertEqual(response.data[0]["description"], "First course for testing.")
        self.assertEqual(response.data[0]["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data[0]["created_at"])
        self.assertIsNotNone(response.data[0]["updated_at"])
        self.assertEqual(response.data[1]["title"], "Test Second Course")
        self.assertEqual(response.data[1]["description"], "Second course for testing.")
        self.assertEqual(response.data[1]["instructor"], self.instructor.id)
        self.assertIsNotNone(response.data[1]["created_at"])
        self.assertIsNotNone(response.data[1]["updated_at"])

    def test_list_courses_login_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.course_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "Test First Course")
        self.assertEqual(response.data[0]["description"], "First course for testing.")
        self.assertEqual(response.data[0]["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data[0]["created_at"])
        self.assertIsNotNone(response.data[0]["updated_at"])
        self.assertEqual(response.data[1]["title"], "Test Second Course")
        self.assertEqual(response.data[1]["description"], "Second course for testing.")
        self.assertEqual(response.data[1]["instructor"], self.instructor.id)
        self.assertIsNotNone(response.data[1]["created_at"])
        self.assertIsNotNone(response.data[1]["updated_at"])

    def test_list_courses_login_student_of_lesson(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.course_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "Test First Course")
        self.assertEqual(response.data[0]["description"], "First course for testing.")
        self.assertEqual(response.data[0]["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data[0]["created_at"])
        self.assertIsNotNone(response.data[0]["updated_at"])
        self.assertEqual(response.data[1]["title"], "Test Second Course")
        self.assertEqual(response.data[1]["description"], "Second course for testing.")
        self.assertEqual(response.data[1]["instructor"], self.instructor.id)
        self.assertIsNotNone(response.data[1]["created_at"])
        self.assertIsNotNone(response.data[1]["updated_at"])

    def test_list_courses_login_instructor_of_lesson(self):
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.get(self.course_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "Test First Course")
        self.assertEqual(response.data[0]["description"], "First course for testing.")
        self.assertEqual(response.data[0]["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data[0]["created_at"])
        self.assertIsNotNone(response.data[0]["updated_at"])
        self.assertEqual(response.data[1]["title"], "Test Second Course")
        self.assertEqual(response.data[1]["description"], "Second course for testing.")
        self.assertEqual(response.data[1]["instructor"], self.instructor.id)
        self.assertIsNotNone(response.data[1]["created_at"])
        self.assertIsNotNone(response.data[1]["updated_at"])

    def test_list_courses_login_another_instructor(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self.course_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "Test First Course")
        self.assertEqual(response.data[0]["description"], "First course for testing.")
        self.assertEqual(response.data[0]["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data[0]["created_at"])
        self.assertIsNotNone(response.data[0]["updated_at"])
        self.assertEqual(response.data[1]["title"], "Test Second Course")
        self.assertEqual(response.data[1]["description"], "Second course for testing.")
        self.assertEqual(response.data[1]["instructor"], self.instructor.id)
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

    def test_create_course_login_normal_user(self):
        data = {
            "title": "New Course",
            "description": "New course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(self.course_list, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_create_course_login_student_of_lesson(self):
        data = {
            "title": "New Course",
            "description": "New course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.course_list, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_create_course_login_instructor_of_lesson(self):
        data = {
            "title": "New Course",
            "description": "New course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.post(self.course_list, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["id"], 3)
        self.assertEqual(response.data["title"], "New Course")
        self.assertEqual(response.data["description"], "New course description.")
        self.assertEqual(response.data["instructor"], self.normal_user.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_create_course_login_another_instructor(self):
        data = {
            "title": "New Course",
            "description": "New course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.course_list, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_retrieve_course_not_login_user(self):
        response = self.client.get(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.first_course.title)
        self.assertEqual(response.data["description"], self.first_course.description)
        self.assertEqual(response.data["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_retrieve_course_login_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.first_course.title)
        self.assertEqual(response.data["description"], self.first_course.description)
        self.assertEqual(response.data["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_retrieve_course_login_student(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.first_course.title)
        self.assertEqual(response.data["description"], self.first_course.description)
        self.assertEqual(response.data["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_retrieve_course_login_instructor_of_lesson(self):
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.get(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.first_course.title)
        self.assertEqual(response.data["description"], self.first_course.description)
        self.assertEqual(response.data["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_retrieve_course_login_another_instructor(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.first_course.title)
        self.assertEqual(response.data["description"], self.first_course.description)
        self.assertEqual(response.data["instructor"], self.instructor_of_lesson.id)
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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_update_course_login_student(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.student)
        response = self.client.put(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_update_course_login_instructor_of_lesson(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
            "instructor": self.instructor.id,
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.put(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Course")
        self.assertEqual(response.data["description"], "Updated Course description.")
        self.assertEqual(response.data["instructor"], self.instructor.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_update_course_login_another_instructor(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.put(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_update_course_without_instructor(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.put(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Course")
        self.assertEqual(response.data["description"], "Updated Course description.")
        self.assertEqual(response.data["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_update_course_without_title(self):
        data = {
            "description": "Updated Course description.",
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.put(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["title"][0], "This field is required.")

    def test_update_course_without_description(self):
        data = {
            "title": "Updated Course",
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.put(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["description"][0], "This field is required.")

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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_partial_update_course_login_student(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.student)
        response = self.client.patch(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_partial_update_course_login_instructor_of_lesson(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
            "instructor": self.instructor.id,
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.patch(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Course")
        self.assertEqual(response.data["description"], "Updated Course description.")
        self.assertEqual(response.data["instructor"], self.instructor.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_partial_update_course_login_another_instructor(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
            "instructor": self.normal_user.id,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.patch(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_partial_update_course_without_instructor(self):
        data = {
            "title": "Updated Course",
            "description": "Updated Course description.",
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.patch(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Course")
        self.assertEqual(response.data["description"], "Updated Course description.")
        self.assertEqual(response.data["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_partial_update_course_without_title(self):
        data = {
            "description": "Updated Course description.",
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.patch(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test First Course")
        self.assertEqual(response.data["description"], "Updated Course description.")
        self.assertEqual(response.data["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_partial_update_course_without_description(self):
        data = {
            "title": "Updated Course",
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.patch(self.first_course_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Course")
        self.assertEqual(response.data["description"], "First course for testing.")
        self.assertEqual(response.data["instructor"], self.instructor_of_lesson.id)
        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    def test_delete_course_not_login_user(self):
        response = self.client.delete(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_delete_course_login_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.delete(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_delete_course_login_student(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.delete(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_delete_course_login_instructor_of_lesson(self):
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.delete(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_course_login_another_instructor(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.delete(self.first_course_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )
