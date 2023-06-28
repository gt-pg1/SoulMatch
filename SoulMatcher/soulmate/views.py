import uuid

from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .serializers import UserSerializer
from .email_sender import send_verification_email


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