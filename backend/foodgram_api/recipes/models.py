from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from api.consts import (
    MIN_INGREDIENT_VALUE,
    MAX_INGREDIENT_VALUE,
    MIN_COOKING_TIME,
    MAX_COOKING_TIME
)

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингридиента"""

    name = models.CharField(
        verbose_name='Название',
        max_length=128
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=64
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name', )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта"""

    name = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/',
        blank=True, null=False
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(
                limit_value=MIN_COOKING_TIME,
                message='Время приготовления - минимум 1 минута.'
            ),
            MaxValueValidator(
                limit_value=MAX_COOKING_TIME,
                message='Время приготовления - максимум 32000 минут.'
            ),
        )
    )
    pub_date = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата публикации'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredient',
        related_name='ingredients'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}'


class RecipeIngredient(models.Model):
    """Модель связи рецептов и ингридиентов"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredient'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(
                limit_value=MIN_INGREDIENT_VALUE,
                message='Количество должно быть больше 0'
            ),
            MaxValueValidator(
                limit_value=MAX_INGREDIENT_VALUE,
                message='Количество должно быть меньше 32001'
            ),
        )
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='Для каждого рецепта должны быть уникальные ингридиенты'
            )
        ]
        ordering = ('recipe__pub_date', 'ingredient__name')

    def __str__(self):
        return (f'{self.recipe}: {self.ingredient.name},'
                f' {self.amount} {self.ingredient.measurement_unit}')


class BaseModel(models.Model):
    """Базовая модель для корзины и избранного"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепты',
    )

    class Meta:
        abstract = True
        constraints = (
            UniqueConstraint(
                fields=('user', 'recipe'),
                name=(
                    'В корзине и избранном должны быть '
                    'только уникальные рецепты'
                )
            ),
        )
        ordering = ('user__username', 'recipe__name',)


class Favorite(BaseModel):
    """Модель для избранного"""

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'

    def __str__(self):
        return f'{self.recipe} в избранном {self.user}'


class ShoppingCart(BaseModel):
    """Модель для корзины"""

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        default_related_name = 'shopping_carts'

    def __str__(self):
        return f'{self.recipe} в корзине {self.user}'
