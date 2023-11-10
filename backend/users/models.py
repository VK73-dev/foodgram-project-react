from django.contrib.auth.models import AbstractUser
from django.db import models

from users.validators import username_validator

MAX_LENGTH_NAME = 150
MAX_LENGTH_EMAIL = 254


class User(AbstractUser):
    username = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Имя пользователя',
        unique=True,
        validators=(username_validator, ),
    )
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        verbose_name='Почта',
        unique=True,
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Имя',
        blank=False,
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Фамилия',
        blank=False,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        default_related_name = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username', )

    def __str__(self):
        return self.username


class Subscription(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscriber',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='author',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='user_author_unique'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='author_and_user_different'
            ),
        )

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
