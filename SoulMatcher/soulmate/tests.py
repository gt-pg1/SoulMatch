from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APITestCase
from rest_framework import status

from .models import CustomUser
from .serializers import UserSerializer

User = get_user_model()


class UserSerializerTest(TestCase):
    def test_user_serializer(self):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        serializer = UserSerializer(user)

        self.assertEqual(set(serializer.data.keys()), {'id', 'username', 'email'})

        self.assertEqual(serializer.data['username'], user.username)
        self.assertEqual(serializer.data['email'], user.email)


class AuthenticationTest(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpassword',
            email_confirmed=False
        )

    def test_authentication_with_unconfirmed_email(self):
        response = self.client.post('/api/soulmate/token/', {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_with_confirmed_email(self):
        # Mark the email as verified
        self.user.email_confirmed = True
        self.user.save()

        # Try to authenticate
        response = self.client.post('/api/soulmate/token/', {
            'username': 'testuser',
            'password': 'testpassword'
        })
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.json())

        # Try accessing protected view
        access_token = response.json()['access']
        response = self.client.get('/api/soulmate/temp_protected_view/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
