import time

from django.urls import reverse

from rest_framework import status

from .base import BaseTestCase
from ..models import CustomUser, Priority, Aspect, Attitude, Weight


class CompatibleUsersViewTestCase(BaseTestCase):
    """
    Тесты для представления CompatibleUsersView.
    """

    def setUp(self):
        """
        Подготовка данных для тестов.
        """
        self.aspect1 = Aspect.objects.create(aspect="Aspect 1")
        self.aspect2 = Aspect.objects.create(aspect="Aspect 2")

        self.weight = Weight.objects.create(weight=1)

        self.attitude_positive = Attitude.objects.create(attitude="positive")
        self.attitude_negative = Attitude.objects.create(attitude="negative")

        self.user1 = self.create_custom_user(username="user1", email="user1@example.com")
        self.user2 = self.create_custom_user(username="user2", email="user2@example.com")

    def create_custom_user(self, username, email):
        """
        Создание пользователя.
        """
        return CustomUser.objects.create(username=username, email=email)

    def create_priority(self, user, aspect, weight, attitude):
        """
        Создание приоритета для пользователя.
        """
        priority = Priority.objects.create(aspect=aspect, weight=weight, attitude=attitude)
        priority.users.add(user)
        return priority

    def test_different_aspects(self):
        """
        Тестирование ситуации, когда у пользователей разные аспекты ->
        -> Не должны быть в одном списке
        """
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect2, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['compatible_users']), 0)

    def test_identical_aspects(self):
        """
        Тестирование ситуации, когда у пользователей идентичные аспекты ->
        -> Должны быть в одном списке и иметь сходство 100
        """
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['compatible_users']), 1)
        self.assertEqual(response.data['compatible_users'][0]['compatibility_percentage'], 100)

    def test_different_attitudes(self):
        """
        Тестирование ситуации, когда у пользователей разные отношения к аспекту  ->
        -> Не должны быть в одном списке
        """
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_negative)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['compatible_users']), 0)

    def test_no_priorities(self):
        """
        Тестирование ситуации, когда у пользователя отсутствуют приоритеты ->
        -> Невозможно просчитать схожих пользователей
        """
        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_many_users_same_priorities(self):
        """
        Тестирование ситуации, когда у множества пользователей одинаковые приоритеты ->
        -> 20 из них попадают в список
        """
        users = [self.create_custom_user(username=f"user{i}", email=f"user{i}@example.com") for i in range(3, 33)]
        for user in users:
            self.create_priority(user, self.aspect1, self.weight, self.attitude_positive)

        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['compatible_users']), 20)

    def test_self_compatibility(self):
        """
        Тестирование отсутствия самого пользователя в списке подходящих ему людей ->
        -> Его не должно быть в выводе
        """
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.user1.id, [user['user_id'] for user in response.data['compatible_users']])

    def test_same_aspects_different_weights(self):
        """
        Тестирование ситуации, когда у пользователей одинаковые аспекты, но разные веса ->
        Пользователь должен оказаться в подходящих
        """
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)

        weight2 = Weight.objects.create(weight=2)
        self.create_priority(self.user2, self.aspect1, weight2, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user2.id, [user['user_id'] for user in response.data['compatible_users']])

    def test_low_compatibility_rate_case(self):
        """
        Тестирование ситуации низкой степени совместимости ->
        Пользователя с совместимостью 50% не должно быть в списке
        """
        self.create_priority(self.user1, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user1, self.aspect2, self.weight, self.attitude_negative)

        self.create_priority(self.user2, self.aspect1, self.weight, self.attitude_positive)
        self.create_priority(self.user2, self.aspect2, self.weight, self.attitude_positive)

        url = reverse('compatible-users', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.user2.id, [user['user_id'] for user in response.data['compatible_users']])

    def test_sorted_order(self):
        """
        Тестирование соблюдения сортировки от более высокой совместимости, к более низкой
        """
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
        """
        Тестирование ситуации, когда совместимость составляет 75% ->
        Такой пользователь должен проходить в список
        """
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

    def test_same_compatibility_percentage(self):
        """
        Тестирование ситуации, когда у пользователей одинаковые проценты совместимости ->
        Оба должны попасть в список
        """
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
        """
        Тестирование ситуации с большим количеством аспектов ->
        1000 приоритетов должны обработаться менее чем за секунду
        """
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
