import uuid
from collections import defaultdict
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Prefetch
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

    def get_user_vector(self, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        priorities = Priority.objects.filter(users=user)
        aspect_indices = {aspect.id: i for i, aspect in enumerate(Aspect.objects.all())}
        user_aspect_ids = [priority.aspect.id for priority in priorities]
        user_vector = [0] * len(aspect_indices)
        for priority in priorities:
            index = aspect_indices[priority.aspect.id]
            user_vector[
                index] = priority.weight.weight if priority.attitude.attitude == 'positive' else -priority.weight.weight
        return user_vector, aspect_indices, user_aspect_ids

    def get(self, request, user_id):
        user_vector, aspect_indices, user_aspect_ids = self.get_user_vector(user_id)

        if not any(user_vector):
            return Response({"error": "User does not have any priorities."}, status=status.HTTP_400_BAD_REQUEST)

        test = Priority.objects.filter(aspect__id__in=user_aspect_ids)

        # Получаем ID пользователей, которые имеют приоритеты по тем же аспектам
        relevant_user_ids = Priority.objects.filter(aspect__id__in=user_aspect_ids).exclude(
            users__id=user_id).values_list('users__id', flat=True).distinct()

        # Получаем приоритеты этих пользователей
        all_priorities = Priority.objects.filter(users__id__in=relevant_user_ids).values(
            'users__id', 'aspect__id', 'weight__weight', 'attitude__attitude')

        vectors = defaultdict(lambda: [0] * len(aspect_indices))

        counter = 0
        x = datetime.now()
        print(f'{x} Начало итерации цикла')
        for priority in all_priorities:
            user_id = priority['users__id']
            aspect_id = priority['aspect__id']
            weight = priority['weight__weight']
            attitude = priority['attitude__attitude']
            index = aspect_indices[aspect_id]
            vectors[user_id][index] = weight if attitude == 'positive' else -weight

            counter += 1
            print(f'{datetime.now()} Итерация {counter}, время итерирования {datetime.now() - x}')

        print(f'{datetime.now()} Конец итерации циклов, время итерирования {datetime.now() - x}')

        similarities = cosine_similarity([user_vector], list(vectors.values()))[0]
        compatible_users = [
            (user_id, (similarity + 1) / 2 * 100)
            for user_id, similarity in zip(vectors.keys(), similarities) if (similarity + 1) / 2 * 100 > 75
        ]
        compatible_users = sorted(compatible_users, key=lambda x: x[1], reverse=True)

        top_20_compatible_users = compatible_users[:20]

        return Response({"compatible_users": top_20_compatible_users}, status=status.HTTP_200_OK)