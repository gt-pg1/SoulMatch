from django.urls import reverse

from rest_framework import status

from .base import BaseTestCase
from ..models import Priority, Aspect, Attitude, Weight


class PrioritiesTest(BaseTestCase):
    """
    Тесты приоритетов.
    """

    def setUp(self):
        """
        Подготовка данных для тестов.
        """
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
        """
        Установка авторизации с токеном доступа.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def get_priority_url(self, priority_id):
        """
        Получение URL для приоритета с указанным идентификатором.
        """
        return reverse('Priorities-detail', kwargs={'pk': priority_id})

    def create_priority(self, aspect, attitude, weight):
        """
        Создание приоритета (POST).
        """
        url = reverse('Priorities-list')
        data = {
            'aspect': aspect,
            'attitude': attitude,
            'weight': weight
        }
        self.set_authorization()
        return self.client.post(url, data)

    def create_priority_object(self, aspect='smoking', attitude='positive', weight=8):
        """
        Создание объекта приоритета.
        """
        aspect_instance, _ = Aspect.objects.get_or_create(aspect=aspect)
        attitude_instance, _ = Attitude.objects.get_or_create(attitude=attitude)
        weight_instance, _ = Weight.objects.get_or_create(weight=weight)

        priority = Priority.objects.create(
            aspect=aspect_instance,
            attitude=attitude_instance,
            weight=weight_instance
        )
        priority.users.add(self.user)

        return priority

    def update_priority(self, priority_id, aspect, attitude, weight):
        """
        Обновление приоритета (PUT).
        """
        url = self.get_priority_url(priority_id)
        data = {
            'aspect': aspect,
            'attitude': attitude,
            'weight': weight
        }
        self.set_authorization()
        return self.client.put(url, data)

    def patch_priority(self, priority_id, data):
        """
        Частичное обновление приоритета (PATCH).
        """
        url = self.get_priority_url(priority_id)
        self.set_authorization()
        return self.client.patch(url, data)

    def delete_priority(self, priority_id):
        """
        Удаление приоритета (DELETE).
        """
        url = self.get_priority_url(priority_id)
        self.set_authorization()
        return self.client.delete(url)

    def test_create_priority(self):
        """
        POST
        Тестирование создания приоритета.
        """
        response = self.create_priority('smoking', 'positive', 8)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_priorities(self):
        """
        GET
        Тестирование получения списка приоритетов.
        """
        url = reverse('Priorities-list')
        self.set_authorization()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_priority(self):
        """
        PUT
        Тестирование обновления приоритета.
        """
        priority = self.create_priority_object()
        response = self.update_priority(priority.id, 'smoking', 'negative', 10)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_priority(self):
        """
        PATCH
        Тестирование частичного обновления приоритета.
        """
        priority = self.create_priority_object()
        response = self.patch_priority(priority.id, {'weight': 7})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_priority(self):
        """
        DELETE
        Тестирование удаления приоритета.
        """
        priority = self.create_priority_object()
        response = self.delete_priority(priority.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_priority_invalid_aspect(self):
        """
        Тестирование создания приоритета с недопустимым аспектом.
        """
        response = self.create_priority('x' * 101, 'negative', 10)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_priority_invalid_attitude(self):
        """
        Тестирование создания приоритета с недопустимым отношением.
        """
        response = self.create_priority('smoking', 'invalid', 10)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_priority_invalid_weight(self):
        """
        Тестирование создания приоритета с недопустимым весом.
        """
        response = self.create_priority('smoking', 'negative', 12)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_priority_invalid_data(self):
        """
        Тестирование обновления приоритета с недопустимыми данными.
        """
        priority = self.create_priority_object()
        response = self.update_priority(priority.id, 'smoking', 'invalid', 12)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

