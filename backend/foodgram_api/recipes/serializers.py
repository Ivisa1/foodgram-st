from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Ingredient, RecipeIngredient, Recipe


User = get_user_model()


class UserSerializer(DjoserUserSerializer):
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
        return (request
                and request.user.is_authenticated
                and user.authors.filter(subscriber=request.user).exists())


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class ReadRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор связи рецепт-ингридиент при чтении"""

    ingredient = IngredientSerializer(read_only=True)
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')

    def to_representation(self, instance):
        """Формат вывода данных"""
        return {
            'id': instance.ingredient.id,
            'name': instance.ingredient.name,
            'measurement_unit': instance.ingredient.measurement_unit,
            'amount': instance.amount
        }


class CreateRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор связи рецепт-ингридиент при создании/изменении"""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов при чтении"""

    author = UserSerializer(read_only=True)
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
                ingredient=x['ingredient'],
                amount=x['amount'],
            )
            for x in ingredients
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


class UserRecipesSerializer(UserSerializer):
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
        recipes_limit = int(request.query_params.get('recipes_limit', '10000'))
        return ShortRecipeSerializer(
            obj.recipes.all()[:recipes_limit], many=True, context=self.context
        ).data
