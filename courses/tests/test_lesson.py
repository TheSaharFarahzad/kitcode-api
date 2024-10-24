from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User
from courses.models import Course, Lesson


class LessonTests(APITestCase):
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

        self.course = Course.objects.create(
            title="Test Course",
            description="A course for testing.",
            instructor=self.instructor_of_lesson,
        )

        self.course.students.set([self.student])

        self.first_lesson = Lesson.objects.create(
            title="First Lesson",
            content="Content of the first lesson.",
            order=1,
            course=self.course,
        )

        self.second_lesson = Lesson.objects.create(
            title="Second Lesson",
            content="Content of the second lesson.",
            order=2,
            course=self.course,
        )

        self.lesson_list = reverse("lesson-list")
        self.first_lesson_detail = reverse(
            "lesson-detail",
            kwargs={"pk": self.first_lesson.id},
        )

    def test_list_lessons_not_login_user(self):
        response = self.client.get(self.lesson_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_list_lessons_login_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.lesson_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_lessons_login_student_of_lesson(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.lesson_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "First Lesson")
        self.assertEqual(response.data[0]["content"], "Content of the first lesson.")
        self.assertEqual(response.data[0]["course"], self.course.id)
        self.assertEqual(response.data[0]["order"], 1)
        self.assertEqual(response.data[1]["title"], "Second Lesson")
        self.assertEqual(response.data[1]["content"], "Content of the second lesson.")
        self.assertEqual(response.data[1]["course"], self.course.id)
        self.assertIsNotNone(response.data[1]["order"], 2)

    def test_list_lessons_login_instructor_of_lesson(self):
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.get(self.lesson_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "First Lesson")
        self.assertEqual(response.data[0]["content"], "Content of the first lesson.")
        self.assertEqual(response.data[0]["course"], self.course.id)
        self.assertEqual(response.data[0]["order"], 1)
        self.assertEqual(response.data[1]["title"], "Second Lesson")
        self.assertEqual(response.data[1]["content"], "Content of the second lesson.")
        self.assertEqual(response.data[1]["course"], self.course.id)
        self.assertIsNotNone(response.data[1]["order"], 2)

    def test_list_lessons_login_another_instructor(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self.lesson_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_lessons_login_another_instructor_student_of_lesson(self):
        self.course.students.set([self.instructor])
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self.lesson_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], "First Lesson")
        self.assertEqual(response.data[0]["content"], "Content of the first lesson.")
        self.assertEqual(response.data[0]["course"], self.course.id)
        self.assertEqual(response.data[0]["order"], 1)
        self.assertEqual(response.data[1]["title"], "Second Lesson")
        self.assertEqual(response.data[1]["content"], "Content of the second lesson.")
        self.assertEqual(response.data[1]["course"], self.course.id)
        self.assertIsNotNone(response.data[1]["order"], 2)

    def test_create_lesson_not_login_user(self):
        data = {
            "title": "New Lesson",
            "content": "Content of the new lesson.",
            "order": 3,
            "course": self.course.id,
        }
        response = self.client.post(self.lesson_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_create_lesson_login_normal_user(self):
        data = {
            "title": "New Lesson",
            "content": "Content of the new lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(self.lesson_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_create_lesson_login_student(self):
        data = {
            "title": "New Lesson",
            "content": "Content of the new lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.lesson_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_create_lesson_login_instructor(self):
        data = {
            "title": "New Lesson",
            "content": "Content of the new lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.lesson_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Lesson")
        self.assertEqual(response.data["content"], "Content of the new lesson.")
        self.assertEqual(response.data["course"], self.course.id)
        self.assertEqual(response.data["order"], 3)

    def test_create_lesson_repeat_order(self):
        data = {
            "title": "New Lesson",
            "content": "Content of the new lesson.",
            "order": 1,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.lesson_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["order"][0], "This order exists.")

    def test_create_lesson_without_title(self):
        data = {
            "title": "",
            "content": "Content of the new lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.lesson_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["title"][0], "This field may not be blank.")

    def test_create_lesson_without_content(self):
        data = {
            "title": "New Lesson",
            "content": "",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.lesson_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["content"][0], "This field may not be blank.")

    def test_create_lesson_without_order(self):
        data = {
            "title": "New Lesson",
            "content": "",
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.lesson_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["order"][0], "This field is required.")

    def test_create_lesson_without_course(self):
        data = {
            "title": "New Lesson",
            "content": "",
            "order": 3,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.lesson_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["course"][0], "This field is required.")

    def test_create_lesson_for_non_existent_course(self):
        data = {
            "title": "New Lesson",
            "content": "Content of the new lesson.",
            "order": 2,
            "course": 99999,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.lesson_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["course"][0], 'Invalid pk "99999" - object does not exist.'
        )

    def test_retrieve_lesson_not_login_user(self):
        response = self.client.get(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_retrieve_lesson_login_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "No Lesson matches the given query.")

    def test_retrieve_lesson_login_student(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "First Lesson")
        self.assertEqual(response.data["content"], "Content of the first lesson.")
        self.assertEqual(response.data["course"], self.course.id)
        self.assertEqual(response.data["order"], 1)

    def test_retrieve_lesson_login_instructor_of_lesson(self):
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.get(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "First Lesson")
        self.assertEqual(response.data["content"], "Content of the first lesson.")
        self.assertEqual(response.data["course"], self.course.id)
        self.assertEqual(response.data["order"], 1)

    def test_retrieve_lesson_login_another_instructor(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "No Lesson matches the given query.")

    def test_retrieve_lesson_login_another_instructor_student_of_lesson(self):
        self.course.students.set([self.instructor])
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "First Lesson")
        self.assertEqual(response.data["content"], "Content of the first lesson.")
        self.assertEqual(response.data["course"], self.course.id)
        self.assertEqual(response.data["order"], 1)

    def test_update_lesson_not_login_user(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        response = self.client.put(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_update_lesson_login_normal_user(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.put(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_update_lesson_login_student(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.student)
        response = self.client.put(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_update_lesson_login_instructor_of_lesson(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.put(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Lesson")
        self.assertEqual(response.data["content"], "Content of the Updated lesson.")
        self.assertEqual(response.data["course"], self.course.id)
        self.assertEqual(response.data["order"], 3)

    def test_update_lesson_login_another_instructor(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.put(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "No Lesson matches the given query.",
        )

    def test_update_lesson_login_another_instructor_student_of_lesson(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.course.students.set([self.instructor])
        self.client.force_authenticate(user=self.instructor)
        response = self.client.put(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_partial_update_lesson_not_login_user(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        response = self.client.patch(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_partial_update_lesson_login_normal_user(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.patch(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_partial_update_lesson_login_student(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.student)
        response = self.client.patch(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_partial_update_lesson_login_instructor_of_lesson(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.patch(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Lesson")
        self.assertEqual(response.data["content"], "Content of the Updated lesson.")
        self.assertEqual(response.data["course"], self.course.id)
        self.assertEqual(response.data["order"], 3)

    def test_partial_update_lesson_login_another_instructor(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.client.force_authenticate(user=self.instructor)
        response = self.client.patch(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "No Lesson matches the given query.",
        )

    def test_partial_update_lesson_login_another_instructor_student_of_lesson(self):
        data = {
            "title": "Updated Lesson",
            "content": "Content of the Updated lesson.",
            "order": 3,
            "course": self.course.id,
        }
        self.course.students.set([self.instructor])
        self.client.force_authenticate(user=self.instructor)
        response = self.client.patch(self.first_lesson_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_delete_lesson_not_login_user(self):
        response = self.client.delete(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_delete_lesson_login_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.delete(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_delete_lesson_login_student(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.delete(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_delete_lesson_login_instructor_of_lesson(self):
        self.client.force_authenticate(user=self.instructor_of_lesson)
        response = self.client.delete(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_lesson_login_another_instructor(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.delete(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "No Lesson matches the given query.",
        )

    def test_delete_lesson_login_another_instructor_student_of_lesson(self):
        self.course.students.set([self.instructor])
        self.client.force_authenticate(user=self.instructor)
        response = self.client.delete(self.first_lesson_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )
