from rest_framework.test import APITestCase

from ..models import CustomUser


class BaseTestCase(APITestCase):
    """
    Базовый класс для тестов API.

    Этот класс предоставляет базовую настройку для тестов API и общие вспомогательные методы.

    Методы:
    - create_user: Создает нового пользователя с указанными данными.

    """

    def setUp(self):
        """
        Настройка тестового случая.

        Этот метод вызывается перед выполнением каждого метода теста.

        """

        # Код настройки

    def create_user(
            self, username='testuser',
            email='test@example.com',
            password='testpassword',
            email_confirmed=True,
            email_confirmation_token='valid_token_1'):
        """
        Создает нового пользователя с указанными данными.

        Аргументы:
        - username (str): Имя пользователя (по умолчанию: 'testuser').
        - email (str): Адрес электронной почты пользователя (по умолчанию: 'test@example.com').
        - password (str): Пароль пользователя (по умолчанию: 'testpassword').
        - email_confirmed (bool): Флаг подтверждения адреса электронной почты пользователя (по умолчанию: True).
        - email_confirmation_token (str): Токен подтверждения адреса электронной почты пользователя (по умолчанию: 'valid_token_1').

        Возвращает:
        - user (CustomUser): Объект созданного пользователя.

        """
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            email_confirmed=email_confirmed,
            email_confirmation_token=email_confirmation_token
        )
        return user
