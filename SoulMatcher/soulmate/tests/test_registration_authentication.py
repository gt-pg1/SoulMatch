from django.urls import reverse

from rest_framework import status

from .base import BaseTestCase
from ..serializers import UserSerializer


class UserSerializerTest(BaseTestCase):
    """
    Тесты для UserSerializer.
    """

    def setUp(self):
        """
        Подготовка данных для тестов.
        """
        self.user = self.create_user()

    def test_user_serializer(self):
        """
        Тестирование сериализации пользователя.
        """
        serializer = UserSerializer(self.user)

        # Проверка наличия ожидаемых полей
        self.assertEqual(set(serializer.data.keys()), {'id', 'username', 'email'})

        # Проверка соответствия данных сериализатора данным пользователя
        self.assertEqual(serializer.data['username'], self.user.username)
        self.assertEqual(serializer.data['email'], self.user.email)

    def test_email_duplication(self):
        """
        Тестирование дублирования email при регистрации пользователя.
        """
        user_data = {
            'username': 'testuser2',
            'email': self.user.email,
            'password': 'password123'
        }

        response = self.client.post(reverse('register'), data=user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_username_duplication(self):
        """
        Тестирование дублирования имени пользователя при регистрации.
        """
        user_data = {
            'username': self.user.username,
            'email': 'test2@example.com',
            'password': 'password123'
        }

        response = self.client.post(reverse('register'), data=user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailConfirmationTest(BaseTestCase):
    """
    Тесты для подтверждения email.
    """

    def setUp(self):
        """
        Подготовка данных для тестов.
        """
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
        """
        Получение URL для подтверждения email.
        """
        return reverse('email-confirmation', kwargs={'token': token})

    def test_email_already_confirmed(self):
        """
        Тестирование попытки подтверждения уже подтвержденного email.
        """
        url = self.get_email_confirmation_url('valid_token_1')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Email already confirmed'})

    def test_email_confirmation_successful(self):
        """
        Тестирование успешного подтверждения email.
        """
        url = self.get_email_confirmation_url('valid_token_2')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'message': 'Email confirmed successfully'})

        # Проверка, что пользователь теперь имеет подтвержденный email
        self.user_unconfirmed.refresh_from_db()
        self.assertTrue(self.user_unconfirmed.email_confirmed)

    def test_invalid_token(self):
        """
        Тестирование подтверждения email с недопустимым токеном.
        """
        url = self.get_email_confirmation_url('invalid_token')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid token'})


class AuthenticationTest(BaseTestCase):
    """
    Тесты аутентификации пользователя.
    """

    def setUp(self):
        """
        Подготовка данных для тестов.
        """
        self.user = self.create_user(email_confirmed=False)

    def authenticate(self, username, password):
        """
        Выполнение аутентификации пользователя.
        """
        return self.client.post(
            '/api/soulmate/token/',
            {'username': username, 'password': password}
        )

    def set_email_confirmed(self, is_confirmed):
        """
        Установка статуса подтверждения email пользователя.
        """
        self.user.email_confirmed = is_confirmed
        self.user.save()

    def test_authentication_with_unconfirmed_email(self):
        """
        Тестирование аутентификации с неподтвержденным email.
        """
        response = self.authenticate('testuser', 'testpassword')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_defunct_user(self):
        """
        Тестирование аутентификации с недействительным пользователем.
        """
        response = self.authenticate('defunct_user', 'testpassword')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authentication_with_confirmed_email(self):
        """
        Тестирование аутентификации с подтвержденным email.
        """
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
        """
        Тестирование аутентификации с пустыми полями.
        """
        self.set_email_confirmed(True)
        response = self.authenticate('', '')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_with_confirmed_email_empty_password(self):
        """
        Тестирование аутентификации с пустым паролем.
        """
        self.set_email_confirmed(True)
        response = self.authenticate('testuser', '')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authentication_with_confirmed_email_wrong_password(self):
        """
        Тестирование аутентификации с неправильным паролем.
        """
        self.set_email_confirmed(True)
        response = self.authenticate('testuser', 'fdasfsfdafdasds')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authentication_with_confirmed_email_empty_username(self):
        """
        Тестирование аутентификации с пустым именем пользователя.
        """
        self.set_email_confirmed(True)
        response = self.authenticate('', 'testpassword')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
