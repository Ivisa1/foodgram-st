from django.contrib.auth import get_user_model

from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserUserSerializer

from drf_extra_fields.fields import Base64ImageField

from users.models import Follow
from recipes.models import Ingredient, RecipeIngredient, Recipe
from .consts import (
    MIN_INGREDIENT_VALUE,
    MAX_INGREDIENT_VALUE,
    MIN_COOKING_TIME,
    MAX_COOKING_TIME
)

User = get_user_model()


class CustomUserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя"""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, user):
        request = self.context['request']
        return (
            request
            and request.user.is_authenticated
            and user.authors.filter(subscriber=request.user).exists()
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class ReadRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор связи рецепт-ингридиент при чтении"""

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_VALUE,
        max_value=MAX_INGREDIENT_VALUE
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор связи рецепт-ингридиент при создании/изменении"""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_VALUE,
        max_value=MAX_INGREDIENT_VALUE
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов при чтении"""

    author = CustomUserSerializer(read_only=True)
    ingredients = ReadRecipeIngredientSerializer(
        source='recipe_ingredient',
        many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, recipe):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and recipe.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and recipe.shopping_carts.filter(user=request.user).exists()
        )


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов при создании/изменении"""

    ingredients = CreateRecipeIngredientSerializer(
        source='recipe_ingredient', many=True,
    )
    image = Base64ImageField(allow_null=False)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError({'image': 'Обязательное поле.'})
        return image

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Обязательное поле.')
        ids = [ingredient['ingredient'].id for ingredient in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Получены неуникальные рецепты.')
        return ingredients

    def set_recipe_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredient')
        recipe = super().create(validated_data)
        self.set_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredient', None)
        ingredients_data = self.validate_ingredients(ingredients_data)
        instance.recipe_ingredient.all().delete()
        self.set_recipe_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReadRecipeSerializer(
            instance, context={'request': self.context.get('request')}).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Короткий сериализатор рецептов"""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = fields


class UserRecipesSerializer(CustomUserSerializer):
    """Сериализатор рецептов у пользователей"""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = int(request.query_params.get('recipes_limit', '6'))
        return ShortRecipeSerializer(
            obj.recipes.all()[:recipes_limit], many=True, context=self.context
        ).data


class SubscribeSerializer(serializers.ModelSerializer):
    """Проверка подписки"""

    class Meta:
        model = Follow
        fields = (
            "author",
            "subscriber"
        )

    def validate(self, data):
        author = data.get('author')
        subscriber = data.get('subscriber')
        if author == subscriber:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя себя.')
        subscription = subscriber.subscriptions.filter(author=author)
        if subscription.exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного пользователя.')
        return data
