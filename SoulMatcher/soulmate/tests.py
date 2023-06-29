from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from .models import CustomUser, Priority, Aspect, Attitude, Weight
from .serializers import UserSerializer


class BaseTestCase(APITestCase):

    def setUp(self):
        pass

    def create_user(
            self, username='testuser',
            email='test@example.com',
            password='testpassword',
            email_confirmed=True,
            email_confirmation_token='valid_token_1'):
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            email_confirmed=email_confirmed,
            email_confirmation_token=email_confirmation_token
        )
        return user


class UserSerializerTest(BaseTestCase):

    def setUp(self):
        self.user = self.create_user()

    def test_user_serializer(self):
        serializer = UserSerializer(self.user)

        self.assertEqual(set(serializer.data.keys()), {'id', 'username', 'email'})

        self.assertEqual(serializer.data['username'], self.user.username)
        self.assertEqual(serializer.data['email'], self.user.email)

    def test_email_duplication(self):
        user_data = {
            'username': 'testuser2',
            'email': self.user.email,
            'password': 'password123'
        }

        response = self.client.post(reverse('register'), data=user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_username_duplication(self):
        user_data = {
            'username': self.user.username,
            'email': 'test2@example.com',
            'password': 'password123'
        }

        response = self.client.post(reverse('register'), data=user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailConfirmationTest(BaseTestCase):

    def setUp(self):
        self.user_confirmed = self.create_user(
            username='confirmed_user',
            email='confirmed@example.com',
            email_confirmed=True
        )
        self.user_confirmed.save()

        self.user_unconfirmed = self.create_user(
            username='unconfirmed_user',
            email='unconfirmed@example.com',
            email_confirmed=False,
            email_confirmation_token='valid_token_2'
        )
        self.user_unconfirmed.save()

    def get_email_confirmation_url(self, token):
        return reverse('email-confirmation', kwargs={'token': token})

    def test_email_already_confirmed(self):
        url = self.get_email_confirmation_url('valid_token_1')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Email already confirmed'})

    def test_email_confirmation_successful(self):
        url = self.get_email_confirmation_url('valid_token_2')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'message': 'Email confirmed successfully'})

        self.user_unconfirmed.refresh_from_db()
        self.assertTrue(self.user_unconfirmed.email_confirmed)

    def test_invalid_token(self):
        url = self.get_email_confirmation_url('invalid_token')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid token'})


class AuthenticationTest(BaseTestCase):

    def setUp(self):
        self.user = self.create_user(email_confirmed=False)

    def authenticate(self, username, password):
        return self.client.post(
            '/api/soulmate/token/',
            {'username': username, 'password': password}
        )

    def set_email_confirmed(self, is_confirmed):
        self.user.email_confirmed = is_confirmed
        self.user.save()

    def test_authentication_with_unconfirmed_email(self):
        response = self.authenticate('testuser', 'testpassword')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_defunct_user(self):
        response = self.authenticate('defunct_user', 'testpassword')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authentication_with_confirmed_email(self):
        self.set_email_confirmed(True)
        response = self.authenticate('testuser', 'testpassword')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.json())

        access_token = response.json()['access']
        response = self.client.get(
            '/api/soulmate/temp_protected_view/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authentication_with_confirmed_email_empty_fields(self):
        self.set_email_confirmed(True)
        response = self.authenticate('', '')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_with_confirmed_email_empty_password(self):
        self.set_email_confirmed(True)
        response = self.authenticate('testuser', '')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_with_confirmed_email_wrong_password(self):
        self.set_email_confirmed(True)
        response = self.authenticate('testuser', 'fdasfsfdafdasds')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authentication_with_confirmed_email_empty_username(self):
        self.set_email_confirmed(True)
        response = self.authenticate('', 'testpassword')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PrioritiesTest(BaseTestCase):

    def setUp(self):
        self.user = self.create_user()
        response = self.client.post(
            reverse('token_obtain_pair'),
            {
                'username': 'testuser',
                'password': 'testpassword'
            }
        )
        self.token = response.data['access']

    def set_authorization(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def get_priority_url(self, priority_id):
        return reverse('Priorities-detail', kwargs={'pk': priority_id})

    def create_priority(self, aspect, attitude, weight):
        url = reverse('Priorities-list')
        data = {
            'aspect': aspect,
            'attitude': attitude,
            'weight': weight
        }
        self.set_authorization()
        return self.client.post(url, data)

    def create_priority_object(self, aspect='smoking', attitude='positive', weight=8):
        aspect_instance, _ = Aspect.objects.get_or_create(aspect=aspect)
        attitude_instance, _ = Attitude.objects.get_or_create(attitude=attitude)
        weight_instance, _ = Weight.objects.get_or_create(weight=weight)

        # Создание объекта Priority без указания пользователя
        priority = Priority.objects.create(
            aspect=aspect_instance,
            attitude=attitude_instance,
            weight=weight_instance
        )
        # Связывание объекта Priority с пользователем
        priority.users.add(self.user)

        return priority

    def update_priority(self, priority_id, aspect, attitude, weight):
        url = self.get_priority_url(priority_id)
        data = {
            'aspect': aspect,
            'attitude': attitude,
            'weight': weight
        }
        self.set_authorization()
        return self.client.put(url, data)

    def patch_priority(self, priority_id, data):
        url = self.get_priority_url(priority_id)
        self.set_authorization()
        return self.client.patch(url, data)

    def delete_priority(self, priority_id):
        url = self.get_priority_url(priority_id)
        self.set_authorization()
        return self.client.delete(url)

    def test_create_priority(self):
        response = self.create_priority('smoking', 'positive', 8)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_priorities(self):
        url = reverse('Priorities-list')
        self.set_authorization()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_priority(self):
        priority = self.create_priority_object()
        response = self.update_priority(priority.id, 'smoking', 'negative', 10)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_priority(self):
        priority = self.create_priority_object()
        response = self.patch_priority(priority.id, {'weight': 7})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_priority(self):
        priority = self.create_priority_object()
        response = self.delete_priority(priority.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_priority_invalid_aspect(self):
        response = self.create_priority('x' * 101, 'negative', 10)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_priority_invalid_attitude(self):
        response = self.create_priority('smoking', 'invalid', 10)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_priority_invalid_weight(self):
        response = self.create_priority('smoking', 'negative', 12)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_priority_invalid_data(self):
        priority = self.create_priority_object()
        response = self.update_priority(priority.id, 'smoking', 'invalid', 12)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
