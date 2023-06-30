from rest_framework import serializers

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import get_user_model

from .models import CustomUser, Priority, Aspect, Attitude, Weight

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User.

    Fields:
        - id:       ID пользователя
        - username: Имя пользователя
        - email:    Email пользователя
        - password: Пароль пользователя

    Parameters:
        - password: Параметр write_only, обозначает,
                    что поле пароля не будет возвращаться
                    в сериализованных данных

    Methods:
        - create:   Создает нового пользователя
                    и обеспечивает хэширование его пароля
    """

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """
        Создает нового пользователя с хэшированным паролем.

        Args:
            validated_data: Валидированные данные,
                            содержащие информацию о пользователе.

        Returns:
            Созданный объект пользователя.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Персонализированный сериализатор для получения токена.

    Methods:
        - validate: Проверяет валидность данных
                    и дополнительные условия для получения токена.
    """

    def validate(self, attrs):
        """
        Проверяет валидность данных
        и дополнительные условия для получения токена.

        Args:
            attrs: Атрибуты с данными для получения токена.

        Returns:
            Валидированные данные для получения токена.

        Raises:
            serializers.ValidationError: Если email пользователя
                                         не подтвержден.
        """
        data = super().validate(attrs)
        user = CustomUser.objects.get(username=attrs['username'])

        if not user.email_confirmed:
            raise serializers.ValidationError("Email не подтвержден")

        return data


class PrioritySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Priority.

    Fields:
        - id:                ID приоритета
        - aspect:            Аспект приоритета (write_only)
        - attitude:          Отношение к приоритету (write_only)
        - weight:            Вес приоритета (write_only)
        - display_aspect:    Отображаемое значение аспекта (read_only)
        - display_attitude:  Отображаемое значение отношения (read_only)
        - display_weight:    Отображаемое значение веса (read_only)

    Parameters:
        - aspect:            Параметр write_only,
                             обозначает аспект приоритета
        - attitude:          Параметр write_only,
                             обозначает отношение к приоритету
        - weight:            Параметр write_only,
                             обозначает вес приоритета

    Methods:
        - validate_aspect:   Проверяет валидность аспекта
                             и возвращает объект Aspect
        - validate_attitude: Проверяет валидность отношения
                             и возвращает объект Attitude
        - validate_weight:   Проверяет валидность веса
                             и возвращает объект Weight
        - create:            Создает новый приоритет
        - update:            Обновляет существующий приоритет
    """
    aspect = serializers.CharField(write_only=True)
    attitude = serializers.CharField(write_only=True)
    weight = serializers.IntegerField(write_only=True)

    display_aspect = serializers.StringRelatedField(
        source='aspect.aspect', read_only=True
    )
    display_attitude = serializers.StringRelatedField(
        source='attitude.attitude', read_only=True
    )
    display_weight = serializers.StringRelatedField(
        source='weight.weight', read_only=True
    )

    class Meta:
        model = Priority
        fields = [
            'id',
            'aspect',
            'attitude',
            'weight',
            'display_aspect',
            'display_attitude',
            'display_weight'
        ]

    def validate_aspect(self, value):
        """
        Проверяет валидность аспекта и возвращает объект Aspect.

        Args:
            value: Значение аспекта.

        Returns:
            Объект Aspect.

        Raises:
            serializers.ValidationError: Если значение аспекта некорректно.
        """
        if len(value) > 100:
            raise serializers.ValidationError(
                "Максимальная длина аспекта 100 символов"
            )

        aspect, created = Aspect.objects.get_or_create(aspect=value)
        return aspect

    def validate_attitude(self, value):
        """
        Проверяет валидность отношения и возвращает объект Attitude.

        Args:
            value: Значение отношения.

        Returns:
            Объект Attitude.

        Raises:
            serializers.ValidationError: Если значение отношения некорректно.
        """
        ALLOWED_ATTITUDES = {'positive', 'negative'}

        if value not in ALLOWED_ATTITUDES:
            raise serializers.ValidationError(
                "Некорректное значение отношения"
            )

        attitude, created = Attitude.objects.get_or_create(attitude=value)
        return attitude

    def validate_weight(self, value):
        """
        Проверяет валидность веса и возвращает объект Weight.

        Args:
            value: Значение веса.

        Returns:
            Объект Weight.

        Raises:
            serializers.ValidationError: Если значение веса некорректно.
        """
        if not 1 <= value <= 10:
            raise serializers.ValidationError(
                "Вес должен быть в диапазоне от 1 до 10"
            )

        weight, created = Weight.objects.get_or_create(weight=value)
        return weight

    def create(self, validated_data):
        """
        Создает новый приоритет.

        Args:
            validated_data: Валидированные данные,
                            содержащие информацию о приоритете.

        Returns:
            Созданный объект приоритета.
        """
        aspect = validated_data.pop('aspect')
        attitude = validated_data.pop('attitude')
        weight = validated_data.pop('weight')

        priority = Priority.objects.create(
            aspect=aspect,
            attitude=attitude,
            weight=weight
        )

        return priority

    def update(self, instance, validated_data):
        """
        Обновляет существующий приоритет.

        Args:
            instance:       Существующий объект приоритета.
            validated_data: Валидированные данные,
                            содержащие информацию для обновления.

        Returns:
            Обновленный объект приоритета.
        """
        aspect = validated_data.pop('aspect', None)
        attitude = validated_data.pop('attitude', None)
        weight = validated_data.pop('weight', None)

        if aspect is not None:
            instance.aspect = aspect

        if attitude is not None:
            instance.attitude = attitude

        if weight is not None:
            instance.weight = weight

        instance.save()
        return instance
