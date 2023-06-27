from django.contrib.auth import get_user_model
from django.test import TestCase
from .serializers import UserSerializer

User = get_user_model()


class UserSerializerTest(TestCase):
    def test_user_serializer(self):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        serializer = UserSerializer(user)

        self.assertEqual(set(serializer.data.keys()), {'id', 'username', 'email'})

        self.assertEqual(serializer.data['username'], user.username)
        self.assertEqual(serializer.data['email'], user.email)
