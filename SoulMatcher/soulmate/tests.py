from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APITestCase
from rest_framework import status

from .models import CustomUser, Priority
from .serializers import UserSerializer

User = get_user_model()


class UserSerializerTest(TestCase):
    def test_user_serializer(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
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
        self.user.email_confirmed = True
        self.user.save()

        response = self.client.post('/api/soulmate/token/', {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.json())

        access_token = response.json()['access']
        response = self.client.get(
            '/api/soulmate/temp_protected_view/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PrioritiesTestCase(APITestCase):

    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            username='testuser1',
            email='testuser1@example.com',
            password='testpassword',
            email_confirmed=True
        )

        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'testuser1', 'password': 'testpassword'}
        )
        self.token = response.data['access']

    def test_create_priority(self):
        url = reverse('Priorities-list')
        data = {
            'aspect': 'smoking',
            'attitude': 'positive',
            'weight': 8
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_priorities(self):
        url = reverse('Priorities-list')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_priority(self):
        priority = Priority.objects.create(
            user=self.user1,
            aspect='smoking',
            attitude='positive',
            weight=8
        )

        url = reverse('Priorities-detail', kwargs={'pk': priority.id})
        data = {
            'aspect': 'smoking',
            'attitude': 'negative',
            'weight': 10
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_priority(self):
        priority = Priority.objects.create(
            user=self.user1,
            aspect='smoking',
            attitude='positive',
            weight=8
        )

        url = reverse('Priorities-detail', kwargs={'pk': priority.id})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_priority_invalid_aspect(self):
        url = reverse('Priorities-list')
        data = {
            'aspect': 'x' * 101,
            'attitude': 'negative',
            'weight': 10
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_priority_invalid_attitude(self):
        url = reverse('Priorities-list')
        data = {
            'aspect': 'smoking',
            'attitude': 'invalid',
            'weight': 10
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_priority_invalid_weight(self):
        url = reverse('Priorities-list')
        data = {
            'aspect': 'smoking',
            'attitude': 'negative',
            'weight': 12
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_priority_invalid_data(self):
        priority = Priority.objects.create(
            user=self.user1,
            aspect='smoking',
            attitude='positive',
            weight=8
        )

        url = reverse('Priorities-detail', kwargs={'pk': priority.id})
        data = {
            'aspect': 'smoking',
            'attitude': 'invalid',
            'weight': 12
        }
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
