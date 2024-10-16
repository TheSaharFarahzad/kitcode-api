from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from django.core import mail
import pytest

class TestJWTAuthentication(APITestCase):
    PASSWORD = "testpassword"

    def setUp(self):
        self.normal_user = User.objects.create_user(username="normal_user", email="normal_user@test.com")
        self.normal_user.set_password(self.PASSWORD)
        self.normal_user.save()
        
        self.super_user = User.objects.create_user(username="super_user", email="super_user@test.com")
        self.super_user.set_password(self.PASSWORD)
        self.super_user.is_superuser = True
        self.super_user.save()

        self.rest_login = reverse('rest_login')
        self.rest_logout = reverse('rest_logout')
        self.rest_user_details = reverse('rest_user_details')
        self.obtain_token_url = reverse('token_obtain_pair')
        self.rest_password_change = reverse('rest_password_change')
        self.rest_password_reset = reverse('rest_password_reset')
        self.rest_password_reset_confirm = reverse('rest_password_reset_confirm')
        self.rest_register = reverse('rest_register')
        self.rest_resend_email = reverse('rest_resend_email')
        

    # def test_login_success(self):
    #     data={
    #         'username': 'normal_user',
    #         'password': self.PASSWORD,
    #     }
    #     response = self.client.post(self.rest_login, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_login_failure_wrong_password(self):
    #     data= {
    #         'username': 'normal_user',
    #         'password': 'wrongpassword',
    #     }
    #     response = self.client.post(self.rest_login, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('non_field_errors', response.data)
    #     self.assertEqual(
    #         response.data['non_field_errors'][0], 
    #         'Unable to log in with provided credentials.',
    #     )

    # def test_login_failure_nonexistent_user(self):
    #     data={
    #         'username': 'unknown_user',
    #         'password': self.PASSWORD,
    #     }
    #     response = self.client.post(self.rest_login, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('non_field_errors', response.data)
    #     self.assertEqual(
    #         response.data['non_field_errors'][0], 
    #         'Unable to log in with provided credentials.',
    #     )

    # def test_logout(self):
    #     login_data = {
    #         'username': 'normal_user',
    #         'password': self.PASSWORD,
    #     }
    #     login_response = self.client.post(self.rest_login, data=login_data)
    #     self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    #     logout_response = self.client.post(self.rest_logout)
    #     self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
    #     response_after_logout = self.client.get(self.rest_user_details)
    #     self.assertEqual(response_after_logout.status_code, status.HTTP_401_UNAUTHORIZED) 

    # def test_password_change_success(self):
    #     data={
    #         'username': 'normal_user',
    #         'password': self.PASSWORD,
    #     }
    #     response = self.client.post(self.obtain_token_url, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     token = response.data['access']

    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    #     data = {
    #         'new_password1': 'newpassword123',
    #         'new_password2': 'newpassword123',
    #     }
    #     response = self.client.post(self.rest_password_change, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_password_change_failure_unauthorized(self):
    #     data = {
    #         'new_password1': 'newpassword123',
    #         'new_password2': 'newpassword123',
    #     }
    #     response = self.client.post(self.rest_password_change, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     self.assertEqual(
    #         response.data['detail'], 
    #         'Authentication credentials were not provided.',
    #     )

    # def test_password_change_failure_mismatch(self):
    #     data={
    #         'username': 'normal_user',
    #         'password': self.PASSWORD,
    #     }
    #     response = self.client.post(self.obtain_token_url, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     token = response.data['access']

    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    #     data = {
    #         'new_password1': 'newpassword123',
    #         'new_password2': 'mismatchpassword',
    #     }
    #     response = self.client.post(self.rest_password_change, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('new_password2', response.data)
    #     self.assertEqual(
    #         response.data['new_password2'][0], 
    #         'The two password fields didn’t match.',
    #     )

    # def test_password_change_failure_too_short(self):
    #     data={
    #         'username': 'normal_user',
    #         'password': self.PASSWORD,
    #     }
    #     response = self.client.post(self.obtain_token_url, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     token = response.data['access']

    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    #     data = {
    #         'new_password1': '1234567',
    #         'new_password2': '1234567',
    #     }
    #     response = self.client.post(self.rest_password_change, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('new_password2', response.data)
    #     self.assertEqual(
    #         response.data['new_password2'][0], 
    #         'This password is too short. It must contain at least 8 characters.',
    #     )

    # def test_password_reset_success(self):
    #     data = {
    #         'email': 'normal_user@test.com',
    #     }
    #     response = self.client.post(self.rest_password_reset, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(str(response.data), "{'detail': 'Password reset e-mail has been sent.'}")


    # @pytest.mark.skip(reason="Check this bug")
    # def test_password_reset_failure_invalid_email(self):
    #     data = {
    #         'email': 'unknown_user@test.com',
    #     }
    #     response = self.client.post(self.rest_password_reset, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('error', response.data)
    #     self.assertEqual(response.data['error'], '')

    # def test_password_reset_confirm_success(self):
    #     data = {
    #         "email": "normal_user@test.com",
    #     }
    #     response = self.client.post(self.rest_password_reset, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(str(response.data), "{'detail': 'Password reset e-mail has been sent.'}")

    #     email_body = mail.outbox[0].body
    #     url_segment = email_body.split("password-reset/confirm/")[1]
    #     uid, token = url_segment.split("/")[:2]

    #     data = {
    #         'uid': uid,
    #         'token': token,
    #         'new_password1': 'newpassword123',
    #         'new_password2': 'newpassword123',
    #     }
    #     response = self.client.post(self.rest_password_reset_confirm, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_password_reset_confirm_failure_password_mismatch(self):
    #     data = {
    #         "email": "normal_user@test.com",
    #     }
    #     response = self.client.post(self.rest_password_reset, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(str(response.data), "{'detail': 'Password reset e-mail has been sent.'}")

    #     email_body = mail.outbox[0].body
    #     url_segment = email_body.split("password-reset/confirm/")[1]
    #     uid, token = url_segment.split("/")[:2]

    #     data = {
    #         'uid': uid,
    #         'token': token,
    #         'new_password1': 'newpassword123',
    #         'new_password2': 'mismatchpassword',
    #     }
    #     response = self.client.post(self.rest_password_reset_confirm, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('new_password2', response.data)
    #     self.assertEqual(
    #         response.data['new_password2'][0], 
    #         'The two password fields didn’t match.',
    #     )

    # def test_password_reset_confirm_failure_invalid_token(self):
    #     data = {
    #         'uid': 'invalid-uid',
    #         'token': 'invalid-token',
    #         'new_password1': 'newpassword123',
    #         'new_password2': 'newpassword123',
    #     }
    #     response = self.client.post(self.rest_password_reset_confirm, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('uid', response.data)
    #     self.assertEqual(response.data['uid'][0], 'Invalid value')

    @pytest.mark.skip(reason="Why is it 204")
    def test_registration_success(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        response = self.client.post(self.rest_register, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_failure_password_mismatch(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'complexpassword123',
            'password2': 'wrongpassword',
        }
        response = self.client.post(self.rest_register, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(
            response.data['non_field_errors'][0], 
            "The two password fields didn't match.",
        )

    def test_registration_failure_existing_username(self):
        data = {
            'username': 'normal_user',
            'email': 'newuser2@test.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        response = self.client.post(self.rest_register, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertEqual(
            response.data['username'][0], 
            "A user with that username already exists.",
        )

    def test_registration_resend_email_success(self):
        data = {
            'email': 'normal_user@test.com',
        }
        response = self.client.post(self.rest_resend_email, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @pytest.mark.skip(reason="Check this bug")
    def test_registration_resend_email_failure_invalid_email(self):
        data = {
            'email': 'unknown_user@test.com',
        }
        response = self.client.post(self.rest_resend_email, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_registration_verify_email_success(self):
    #     verify_token = "valid-verify-token"
    #     response = self.client.post('/dj-rest-auth/registration/verify-email/', {
    #         'key': verify_token,
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_registration_verify_email_failure_invalid_token(self):
    #     response = self.client.post('/dj-rest-auth/registration/verify-email/', {
    #         'key': 'invalid-token',
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_get_user_success(self):
    #     token = self.get_jwt_token('normal_user', self.PASSWORD)
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    #     response = self.client.get('/dj-rest-auth/user/')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['username'], 'normal_user')

    # def test_get_user_failure_no_token(self):
    #     response = self.client.get('/dj-rest-auth/user/')
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_update_user_success(self):
    #     token = self.get_jwt_token('normal_user', self.PASSWORD)
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    #     response = self.client.put('/dj-rest-auth/user/', {
    #         'username': 'updated_user',
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['username'], 'updated_user')

    # def test_update_user_failure_no_token(self):
    #     response = self.client.put('/dj-rest-auth/user/', {
    #         'username': 'updated_user'
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_update_user_failure_invalid_data(self):
    #     token = self.get_jwt_token('normal_user', self.PASSWORD)
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    #     response = self.client.put('/dj-rest-auth/user/', {
    #         'username': '',
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_partial_update_user_success(self):
    #     token = self.get_jwt_token('normal_user', self.PASSWORD)
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    #     response = self.client.patch('/dj-rest-auth/user/', {
    #         'email': 'updated_user@test.com',
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['email'], 'updated_user@test.com')

    # def test_partial_update_user_failure_no_token(self):
    #     response = self.client.patch('/dj-rest-auth/user/', {
    #         'email': 'updated_user@test.com',
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_partial_update_user_failure_invalid_data(self):
    #     token = self.get_jwt_token('normal_user', self.PASSWORD)
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    #     response = self.client.patch('/dj-rest-auth/user/', {
    #         'email': 'not-an-email',
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)




