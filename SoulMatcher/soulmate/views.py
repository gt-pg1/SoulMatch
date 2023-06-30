import uuid
from collections import defaultdict

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets, views
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.views import TokenObtainPairView as SimpleTokenObtainPairView

from sklearn.metrics.pairwise import cosine_similarity

from .models import Priority, CustomUser, Aspect
from .serializers import \
    UserSerializer, \
    CustomTokenObtainPairSerializer, \
    PrioritySerializer
from .email_sender import send_verification_email


class CustomTokenObtainPairView(SimpleTokenObtainPairView):
    """
    Пользовательское представление для получения пары токенов. Использует пользовательский сериализатор,
    который добавляет дополнительные данные в ответ.
    """
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Обработка регистрации пользователя.

    Принимает данные пользователя, проверяет их валидность, создает новый экземпляр User и отправляет
    письмо с подтверждением.


    :param request: HTTP-запрос. POST-данные должны содержать данные пользователя.

    :return: Объект Response с сериализованными данными пользователя или ошибками валидации.
    """
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            confirmation_token = str(uuid.uuid4())
            user.email_confirmation_token = confirmation_token
            user.save()
            send_verification_email(request, user, confirmation_token)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def email_confirmation(request, token):
    """
    Подтверждение электронной почты пользователя.

    Если токен действителен и электронная почта не подтверждена, обновляет
    поле email_confirmed пользователя.

    :param request: HTTP-запрос.
    :param token: Строка, представляющая токен подтверждения электронной почты.

    :return: Объект Response с сообщением об успешном подтверждении или ошибкой.
    """
    try:
        user = get_user_model().objects.get(email_confirmation_token=token)

        if user.email_confirmed:
            return Response({'error': 'Email already confirmed'}, status=status.HTTP_400_BAD_REQUEST)

        user.email_confirmed = True
        user.save()
        return Response({'message': 'Email confirmed successfully'}, status=status.HTTP_200_OK)
    except get_user_model().DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def temp_protected_view(request):
    """
    Временное защищенное представление для тестирования.

    Доступно только аутентифицированным пользователям.

    :param request: HTTP-запрос.

    :return: Объект Response с сообщением об успешном доступе.
    """
    return Response({"message": "This is a protected view, you have access."})


class PriorityViewSet(viewsets.ModelViewSet):
    """
    ViewSet для просмотра и редактирования приоритетов пользователя.

    Этот ViewSet предоставляет действия `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` и `list()`.

    Основная цель этого ViewSet - работа с приоритетами аутентифицированного пользователя.
    """
    serializer_class = PrioritySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Возвращает queryset приоритетов для аутентифицированного пользователя.
        """
        user = self.request.user
        return Priority.objects.filter(users__in=[user])

    def perform_create(self, serializer):
        """
        Сохраняет приоритет и связывает его с аутентифицированным пользователем.
        """
        priority = serializer.save()
        priority.users.add(self.request.user)


class CompatibleUsersView(views.APIView):
    """
    Представление для получения списка совместимых пользователей на основе приоритетов.
    """

    def get_user_vector(self, user_id):
        """
        Получает вектор приоритетов для заданного пользователя.

        :param user_id: ID пользователя
        :return: Кортеж, содержащий вектор приоритетов, индексы аспектов и ID аспектов пользователя
        """
        user = get_object_or_404(CustomUser, id=user_id)
        priorities = Priority.objects.filter(users=user)

        # Получение всех аспектов из таблицы и формирование их порядка,
        # для корректной расстановки векторов и последующего рассчета косинусного сходства
        aspect_indices = {aspect.id: i for i, aspect in enumerate(Aspect.objects.all())}

        # Получение всех аспектов клиента и создание шаблона его вектора
        user_aspect_ids = [priority.aspect.id for priority in priorities]
        user_vector = [0] * len(aspect_indices)

        # Разбор приоритетов клиента и формирвание его вектора интересов
        for priority in priorities:
            index = aspect_indices[priority.aspect.id]

            weight = priority.weight.weight
            attitude = priority.attitude.attitude
            user_vector[index] = weight if attitude == 'positive' else -weight

        return user_vector, aspect_indices, user_aspect_ids

    def get(self, request, user_id):
        """
        Обрабатывает GET-запросы для получения списка совместимых пользователей.

        Производит анализ приоритетов пользователей с целью определения степени совместимости.
        Для заданного пользователя ищет других пользователей, у которых есть общие приоритеты,
        и вычисляет степень совместимости на основе косинусного сходства между их векторами приоритетов.

        :param request: Объект запроса
        :param user_id: ID пользователя, для которого необходимо найти совместимых пользователей
        :return: Список совместимых пользователей в порядке убывания степени совместимости
        """
        # user_vector - вектор интересов клиента
        # aspect_indices - словарь с установленным порядком аспектов, для установки порядка в векторах
        # user_aspect_ids - список с аспектами клиента
        user_vector, aspect_indices, user_aspect_ids = self.get_user_vector(user_id)

        if not any(user_vector):
            return Response({"error": "User does not have any priorities."}, status=status.HTTP_400_BAD_REQUEST)

        # Получение всех пользователей с приоритететами клиента
        relevant_user_ids = Priority.objects.filter(
            aspect__id__in=user_aspect_ids
        ).values_list(
            'users__id', flat=True
        ).distinct()

        # Удаление id клиента из списка пользователей
        relevant_user_ids = list(relevant_user_ids)
        if user_id in relevant_user_ids:
            relevant_user_ids.remove(user_id)

        # Получение всех приоритетов пользователей, имеющих общие приоритеты с клиентом
        all_priorities = Priority.objects.filter(
            users__id__in=relevant_user_ids
        ).values(
            'users__id', 'aspect__id', 'weight__weight', 'attitude__attitude'
        )

        # Создание словаря, в котором для каждого несуществующего ключа
        # будет создаваться массив из нулей длиной в количество аспектов в БД
        vectors = defaultdict(lambda: [0] * len(aspect_indices))

        # В цикле по одному перебираются приоритеты, привязанные к пользователю
        # Благордаря defaultdict они подставляются на те позиции, на которых они должны находится
        # в соответствии с aspect_indices. В конце цикла словарь vectors полностью заполняется
        # правильно упорядоченными векторами каждого пользователя
        for priority in all_priorities:
            user_id = priority['users__id']
            aspect_id = priority['aspect__id']
            weight = priority['weight__weight']
            attitude = priority['attitude__attitude']

            index = aspect_indices[aspect_id]
            vectors[user_id][index] = weight if attitude == 'positive' else -weight

        # Если ни одного вектора интересов построить не удалось (не было пользователей, не было пользователей
        # с заполненными интересами), то выполнение алгоритма останавливается
        if not vectors:
            return Response({"compatible_users": []}, status=status.HTTP_200_OK)

        # Рассчет косинусного сходства, формирование массива для вывода результата запроса клиента,
        # нормализация косинусного сходства (до значения до 0 до 100), фильтрация от 75 и ниже и сортировка
        similarities = cosine_similarity([user_vector], list(vectors.values()))[0]
        compatible_users = [
            {
                'user_id': user_id,
                'name': self.get_user_name(user_id),
                'compatibility_percentage': (similarity + 1) / 2 * 100
            }
            for user_id, similarity in zip(vectors.keys(), similarities)
            if (similarity + 1) / 2 * 100 >= 75
        ]
        compatible_users = sorted(compatible_users, key=lambda x: x['compatibility_percentage'], reverse=True)

        return Response({"compatible_users": compatible_users[:20]}, status=status.HTTP_200_OK)

    @staticmethod
    def get_user_name(user_id):
        """
        Возвращает имя пользователя по его ID. Если first_name и last_name отсутствуют, возвращает username.

        :param user_id: ID пользователя
        :return: Имя пользователя
        """
        user = CustomUser.objects.get(id=user_id)
        return f"{user.first_name} {user.last_name}".strip() or user.username
