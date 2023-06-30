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
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
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
    return Response({"message": "This is a protected view, you have access."})


class PriorityViewSet(viewsets.ModelViewSet):
    serializer_class = PrioritySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Priority.objects.filter(users__in=[user])

    def perform_create(self, serializer):
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

        aspect_indices = {aspect.id: i for i, aspect in enumerate(Aspect.objects.all())}

        user_aspect_ids = [priority.aspect.id for priority in priorities]
        user_vector = [0] * len(aspect_indices)

        for priority in priorities:
            index = aspect_indices[priority.aspect.id]

            weight = priority.weight.weight
            attitude = priority.attitude.attitude
            user_vector[index] = weight if attitude == 'positive' else -weight

        return user_vector, aspect_indices, user_aspect_ids

    def get(self, request, user_id):
        """
        Обрабатывает GET-запросы на получение списка совместимых пользователей.

        :param request: Объект запроса
        :param user_id: ID пользователя, для которого необходимо найти совместимых пользователей
        :return: Список совместимых пользователей
        """
        user_vector, aspect_indices, user_aspect_ids = self.get_user_vector(user_id)

        if not any(user_vector):
            return Response({"error": "User does not have any priorities."}, status=status.HTTP_400_BAD_REQUEST)

        relevant_user_ids = Priority.objects.filter(
            aspect__id__in=user_aspect_ids
        ).values_list(
            'users__id', flat=True
        ).distinct()

        relevant_user_ids = list(relevant_user_ids)
        if user_id in relevant_user_ids:
            relevant_user_ids.remove(user_id)

        all_priorities = Priority.objects.filter(
            users__id__in=relevant_user_ids
        ).values(
            'users__id', 'aspect__id', 'weight__weight', 'attitude__attitude'
        )

        vectors = defaultdict(lambda: [0] * len(aspect_indices))

        for priority in all_priorities:
            user_id = priority['users__id']
            aspect_id = priority['aspect__id']
            weight = priority['weight__weight']
            attitude = priority['attitude__attitude']

            index = aspect_indices[aspect_id]
            vectors[user_id][index] = weight if attitude == 'positive' else -weight

        if not vectors:
            return Response({"compatible_users": []}, status=status.HTTP_200_OK)

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
