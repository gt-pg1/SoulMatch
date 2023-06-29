from rest_framework import serializers

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import get_user_model

from .models import CustomUser, Priority, Aspect, Attitude, Weight

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Метод create_user обеспечивает хэширование пароля
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        user = CustomUser.objects.get(username=attrs['username'])

        if not user.email_confirmed:
            raise serializers.ValidationError("Email is not verified")

        return data


class PrioritySerializer(serializers.ModelSerializer):
    aspect = serializers.CharField(write_only=True)
    attitude = serializers.CharField(write_only=True)
    weight = serializers.IntegerField(write_only=True)

    display_aspect = serializers.StringRelatedField(source='aspect.aspect', read_only=True)
    display_attitude = serializers.StringRelatedField(source='attitude.attitude', read_only=True)
    display_weight = serializers.StringRelatedField(source='weight.weight', read_only=True)

    class Meta:
        model = Priority
        fields = ['id', 'aspect', 'attitude', 'weight', 'display_aspect', 'display_attitude', 'display_weight']

    def validate_aspect(self, value):
        aspect, created = Aspect.objects.get_or_create(aspect=value)
        return aspect

    def validate_attitude(self, value):
        attitude, created = Attitude.objects.get_or_create(attitude=value)
        return attitude

    def validate_weight(self, value):
        weight, created = Weight.objects.get_or_create(weight=value)
        return weight

    def create(self, validated_data):
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