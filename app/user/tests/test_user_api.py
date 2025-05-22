"""
Test User endpoints
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


# Public tests - Unaunthenticated requests
class PublicUserApiTests(TestCase):
    """ Test user api public features of the API """

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        payload = {
            "email": "test1@example.com",
            "password": "test123",
            "name": "John Doe"
        }
        res = self.client.post(CREATE_USER_URL, payload)
        # Check user was created
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """
        Test an error is returned if trying to create an
        user with a duplicated email
        """
        payload = {
            "email": "test1@example.com",
            "password": "test123",
            "name": "John Doe"
        }
        create_user(**payload)  # First user
        res = self.client.post(CREATE_USER_URL, payload)  # Duplicate

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password is less than 5 chars"""
        payload = {
            "email": "test1@example.com",
            "password": "tes",
            "name": "John Doe"
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Check user was not created
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that token is generated for valid credentials"""
        user_details = {
            "email": "test1@example.com",
            "password": "test12345",
            "name": "John Doe"
        }
        create_user(**user_details)

        # User credentials
        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test that wron credentials return an error"""
        user_details = {
            "email": "test1@example.com",
            "password": "test12345",
            "name": "John Doe"
        }
        create_user(**user_details)
        payload = {
            'email': user_details['email'],
            'password': "incorrect_pass",
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_blank_password(self):
        """Test that a blank password returns an error"""
        user_details = {
            "email": "test1@example.com",
            "password": "test12345",
            "name": "John Doe"
        }
        create_user(**user_details)
        payload = {
            'email': user_details['email'],
            'password': "",
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_retrieve_user_is_authenticated(self):
        """Test that authentication is required for users"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            email="test1@example.com",
            password="test12345",
            name="John Doe"
        )
        self.client = APIClient()
        # Any request we make to the API from now on is authenticated
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me url"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {
            'name': 'new name',
            'password': 'newpassword123'
        }
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
