from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email = models.EmailField(blank=True, unique=True)
    email_confirmed = models.BooleanField(default=False)
    email_confirmation_token = models.CharField(
        max_length=36,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.username


class Aspect(models.Model):
    aspect = models.CharField(max_length=100)

    def __str__(self):
        return self.aspect


class Attitude(models.Model):
    attitude = models.CharField(
        max_length=10,
        choices=[
            ('positive', 'Положительное'),
            ('negative', 'Отрицательное'),
        ]
    )

    def __str__(self):
        return self.attitude


class Weight(models.Model):
    weight = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 11)]
    )

    def __str__(self):
        return str(self.weight)


class Priority(models.Model):
    aspect = models.ForeignKey(Aspect, on_delete=models.CASCADE)
    attitude = models.ForeignKey(Attitude, on_delete=models.CASCADE)
    weight = models.ForeignKey(Weight, on_delete=models.CASCADE)
    users = models.ManyToManyField(CustomUser)

    def __str__(self):
        return f"{self.aspect} ({self.attitude}, {self.weight})"
