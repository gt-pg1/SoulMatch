from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email_confirmed = models.BooleanField(default=False)
    email_confirmation_token = models.CharField(max_length=36, null=True, blank=True)

    def __str__(self):
        return self.username


class Priority(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    aspect = models.CharField(max_length=100)
    attitude = models.CharField(
        max_length=10,
        choices=[
            ('positive', 'Положительное'),
            ('negative', 'Отрицательное'),
        ]
    )
    weight = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 11)])

    def __str__(self):
        return f"{self.aspect} ({self.attitude}, {self.weight})"
