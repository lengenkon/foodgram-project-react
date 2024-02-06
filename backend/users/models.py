from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_lENGTH_USER = 150


class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name]
    
    first_name = models.CharField('Имя', max_length=MAX_lENGTH_USER)
    last_name = models.CharField('Фамилия', max_length=MAX_lENGTH_USER)
    email = models.EmailField(
        'Электронная почта',
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.'
        },
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


User = get_user_model()


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers")

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.CheckConstraint(
                check=Q(following__ne=F('user')),
                name='subscribe_to_yourself')
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_following',
            )
        ]
