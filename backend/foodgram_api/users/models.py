from django.db import models
from django.contrib.auth.models import AbstractUser

from .validators import username_validator


class User(AbstractUser):
    """Переопределенная модель пользователя"""

    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=150,
        unique=True,
        validators=(username_validator, ),
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=254,
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/user_avatars',
        blank=True, null=False
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username', )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name'
    )

    def __str__(self):
        return f'{self.username}'


class Follow(models.Model):
    """Модель подписок"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор',
        help_text='Автор',
    )
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
        help_text='Подписчик',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('subscriber', 'author'),
                name='Уникальная связь подписчик-автор'
            ),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F('author')),
                name='Исключение самоподписки'
            )
        ]
        ordering = ('author__username', )

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
