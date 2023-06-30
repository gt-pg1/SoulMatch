import time

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


class CompatibleUsersViewTestCase(APITestCase):

    def setUp(self):
        self.aspect1 = Aspect.objects.create(aspect="Aspect 1")
        self.aspect2 = Aspect.objects.create(aspect="Aspect 2")

        self.weight = Weight.objects.create(weight=1)

        self.attitude_positive = Attitude.objects.create(attitude="positive")
        self.attitude_negative = Attitude.objects.create(attitude="negative")

        self.user1 = self.create_custom_user(username="user1", email="user1@example.com")
        self.user2 = self.create_custom_user(username="user2", email="user2@example.com")

    def create_custom_user(self, username, email):
        return CustomUser.objects.create(username=username, email=email)

    def create_priority(self, user, aspect, weight, attitude):
        priority = Priority.objects.create(aspect=aspect, weight=weight, attitude=attitude)
        priority.users.add(user)
        return priority

    def test_different_aspects(self):
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect2, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['compatible_users']), 0)

    def test_identical_aspects(self):
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['compatible_users']), 1)
        self.assertEqual(response.data['compatible_users'][0]['compatibility_percentage'], 100)

    def test_different_attitudes(self):
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_negative)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['compatible_users']), 0)

    def test_no_priorities(self):
        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_many_users_same_priorities(self):
        users = [self.create_custom_user(username=f"user{i}", email=f"user{i}@example.com") for i in range(3, 33)]
        for user in users:
            self.create_priority(user, self.aspect1, self.weight, self.attitude_positive)

        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['compatible_users']), 20)

    def test_self_compatibility(self):
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.user1.id, [user['user_id'] for user in response.data['compatible_users']])

    def test_same_aspects_different_weights(self):
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)

        weight2 = Weight.objects.create(weight=2)
        self.create_priority(self.user2, self.aspect1, weight2, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user2.id, [user['user_id'] for user in response.data['compatible_users']])

    def test_low_compatibility_rate_case(self):
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user1, self.aspect2, self.weight, self.attitude_negative)

        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect2, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.user2.id, [user['user_id'] for user in response.data['compatible_users']])

    def test_single_aspect(self):
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)

        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user2.id, [user['user_id'] for user in response.data['compatible_users']])

    def test_sorted_order(self):
        user3 = self.create_custom_user(username="user3", email="user3@example.com")
        user4 = self.create_custom_user(username="user4", email="user4@example.com")
        aspect3 = Aspect.objects.create(aspect="Aspect 3")
        aspect4 = Aspect.objects.create(aspect="Aspect 4")
        aspect5 = Aspect.objects.create(aspect="Aspect 5")

        weight10 = Weight.objects.create(weight=10)
        weight5 = Weight.objects.create(weight=5)
        weight0 = Weight.objects.create(weight=0)

        # Приоритеты для user1
        self.create_priority(self.user1, self.aspect1, weight10, self.attitude_positive)
        self.create_priority(self.user1, self.aspect2, weight10, self.attitude_positive)
        self.create_priority(self.user1, aspect3, weight10, self.attitude_positive)
        self.create_priority(self.user1, aspect4, weight10, self.attitude_positive)
        self.create_priority(self.user1, aspect5, weight0, self.attitude_positive)

        # Приоритеты для user2 (87.5% совместимости)
        self.create_priority(self.user2, self.aspect1, weight5, self.attitude_positive)
        self.create_priority(self.user2, self.aspect2, weight5, self.attitude_positive)
        self.create_priority(self.user2, aspect3, weight5, self.attitude_positive)
        self.create_priority(self.user2, aspect4, weight0, self.attitude_positive)
        self.create_priority(self.user2, aspect5, weight5, self.attitude_positive)

        # Приоритеты для user3 (90.8% совместимости)
        self.create_priority(user3, self.aspect1, weight5, self.attitude_positive)
        self.create_priority(user3, self.aspect2, weight5, self.attitude_positive)
        self.create_priority(user3, aspect3, weight10, self.attitude_positive)
        self.create_priority(user3, aspect4, weight0, self.attitude_positive)
        self.create_priority(user3, aspect5, weight0, self.attitude_positive)

        # Приоритеты для user4 (93.3% совместимости)
        self.create_priority(user4, self.aspect1, weight5, self.attitude_positive)
        self.create_priority(user4, self.aspect2, weight5, self.attitude_positive)
        self.create_priority(user4, aspect3, weight5, self.attitude_positive)
        self.create_priority(user4, aspect4, weight10, self.attitude_positive)
        self.create_priority(user4, aspect4, weight0, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        compatibilities = [user['compatibility_percentage'] for user in response.data['compatible_users']]
        self.assertEqual(compatibilities, sorted(compatibilities, reverse=True))

    def test_75_percent_compatibility_case(self):
        aspect3 = Aspect.objects.create(aspect="Aspect 3")
        aspect4 = Aspect.objects.create(aspect="Aspect 4")

        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user1, self.aspect2, self.weight, self.attitude_positive)
        self.create_priority(self.user1, aspect3, self.weight, self.attitude_positive)
        self.create_priority(self.user1, aspect4, self.weight, self.attitude_negative)

        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect2, self.weight, self.attitude_positive)
        self.create_priority(self.user2, aspect3, self.weight, self.attitude_positive)
        self.create_priority(self.user2, aspect4, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        compatible_users = [user for user in response.data['compatible_users'] if user['user_id'] == self.user2.id]
        self.assertTrue(compatible_users)
        user2_compatibility = compatible_users[0]['compatibility_percentage']
        self.assertEqual(user2_compatibility, 75)

    def test_incomplete_profiles(self):
        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_compatibility_percentage(self):
        user3 = self.create_custom_user(username="user3", email="user3@example.com")

        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(user3, self.aspect1, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users_in_list = [user['user_id'] for user in response.data['compatible_users']]
        self.assertIn(self.user2.id, users_in_list)
        self.assertIn(user3.id, users_in_list)

    def test_large_number_of_aspects(self):
        for i in range(3, 1001):
            Aspect.objects.create(aspect=f"Aspect {i}")

        for aspect in Aspect.objects.all():
            self.create_priority(self.user1, aspect, self.weight, self.attitude_positive)
            self.create_priority(self.user2, aspect, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})

        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()

        execution_time = end_time - start_time
        max_execution_time = 1

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(execution_time, max_execution_time)
