"""
Tests for /users endpoints
"""
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from time import time

from http.cookies import SimpleCookie
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from users.serializers import UserSerializer
from core.tests.helpers import create_user

CREATE_USER_URL = reverse('users:create')
TOKEN_URL = reverse('users:token')
ME_URL = reverse('users:me')
TOKEN_REFRESH_URL = reverse('users:refresh')


class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = {
            'email': 'test@example.com',
            'password': 'password',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            'email': 'test@example.com',
            'password': 'password',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 chars."""
        payload = {
            'email': 'test@example.com',
            'password': 'pw',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@example.com',
            'password': 'password',
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)

        cookies = dict(res.cookies.items())

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('refresh', res.data)
        self.assertIn('access', res.data)

        self.assertIn('refresh', cookies)
        self.assertIn('HttpOnly;', str(cookies['refresh']))

        self.assertIn('access', cookies)
        self.assertIn('HttpOnly;', str(cookies['access']))

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid."""
        create_user(email='test@example.com', password='goodpass')

        payload = {'email': 'test@example.com', 'password': 'badpass'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_email_not_found(self):
        """Test error returned if user not found for given email."""
        payload = {'email': 'test@example.com', 'password': 'pass123'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {'email': 'test@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.password = 'password'
        self.user = create_user(
            email='test@example.com',
            password=self.password,
            first_name='John',
            last_name='Doe',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
        })

    def test_token_refresh_by_cookie(self):
        """Test token refresh by httponly cookie produces an access token."""
        self.client.force_authenticate(user=self.user)
        self.client.logout()
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies = SimpleCookie({'refresh': str(refresh)})
        res = self.client.post(TOKEN_REFRESH_URL)
        cookies = dict(res.cookies.items())

        self.assertEqual(res.status_code, 200)

        self.assertIn('access', cookies)
        self.assertIn('access', res.data)

    def test_token_refresh(self):
        """Test token refresh by payload."""
        self.client.force_authenticate(user=self.user)
        refresh = RefreshToken.for_user(self.user)
        payload = {'refresh': str(refresh)}

        res = self.client.post(TOKEN_REFRESH_URL, payload)
        cookies = dict(res.cookies.items())

        self.assertEqual(res.status_code, 200)

        self.assertIn('access', cookies)
        self.assertIn('access', res.data)

    def test_empty_token_refresh(self):
        """Test token refresh by payload."""
        self.client.force_authenticate(user=self.user)
        payload = {}

        res = self.client.post(TOKEN_REFRESH_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on users/me."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_without_jwt(self):
        """Test updating the user profile
        for authenticated user requires jwt."""
        payload = {
            'email': 'change@example.com',
            'first_name': 'Antonio',
            'last_name': 'Banderas',
            'password': 'new password',
        }

        res = self.client.put(ME_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_user_profile(self):
        """Test updating the user profile for authenticated user."""
        payload = {
            'last_name': 'Valencia',
        }

        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, payload['last_name'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_password_update_without_jwt(self):
        """Test updating password requires JWT auth."""
        payload = {
            'password': 'new password',
        }

        res = self.client.patch(ME_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_name(self):
        """Test updating the user authenticated name."""
        payload = {
            'last_name': 'Roberts',
            'first_name': 'Marley',
        }

        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, payload['last_name'])
        self.assertEqual(self.user.first_name, payload['first_name'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_user_profile(self):
        """Test updating the user profile for
        authenticated user successful with fresh token."""
        self.client.logout()
        token = AccessToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {str(token)}')

        payload = {
            'email': 'change@example.com',
            'first_name': 'Antonio',
            'last_name': 'Banderas',
            'password': 'new password',
        }

        res = self.client.put(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.first_name, payload['first_name'])
        self.assertEqual(self.user.last_name, payload['last_name'])
        self.assertTrue(self.user.check_password(payload['password']))

    @patch('users.serializers.time.time')
    def test_password_change_on_stale_token(self, patched_time):
        """Test password change requires fresh token"""
        self.client.logout()

        patched_time.return_value = time() + (
            UserSerializer.MINIMUM_IAT_AGE_PWD_CHANGE * 1.5
        )

        token = AccessToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {str(token)}')

        payload = {
            'last_name': 'Valencia',
            'password': 'new password',
        }

        res = self.client.patch(ME_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
