from django.contrib.auth.models import AbstractUser
from django.db import models
# from recipes.models import Follow

class CustomUser(AbstractUser):
    """Переопределенная модель пользователя."""

    first_name = models.CharField("first name", max_length=150)
    last_name = models.CharField("last name", max_length=150)

    # class Roles(models.TextChoices):
    #     USER = 'user'
    #     MODERATOR = 'moderator'
    #     ADMIN = 'admin'

    # role = models.CharField(
    #     'Роль',
    #     max_length=MAX_LENGHT_ROLE,
    #     default=Roles.USER,
    #     choices=Roles.choices,
    # )
    # bio = models.TextField(
    #     'О пользователе',
    #     blank=True,
    # )
    email = models.EmailField(
        'Электронная почта',
        # max_length=MAX_LENGHT_EMAIL,
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.'
        },
    )
    # following = models.ManyToManyField('self', through='Follow')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username