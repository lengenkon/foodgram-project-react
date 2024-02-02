from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Переопределенная модель пользователя."""

    first_name = models.CharField("first name", max_length=150)
    last_name = models.CharField("last name", max_length=150)
    email = models.EmailField(
        'Электронная почта',
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.'
        },
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
