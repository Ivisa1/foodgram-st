from django_filters import rest_framework as filters
from django_filters.filters import ChoiceFilter

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов по назваию"""

    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name', )


class RecipeFilter(filters.FilterSet):
    STATUS_CHOICES = (
        (0, False),
        (1, True),
        (True, True),
        (False, False)
    )

    is_favorited = ChoiceFilter(
        choices=STATUS_CHOICES, method='get_is_favorited')
    is_in_shopping_cart = ChoiceFilter(
        choices=STATUS_CHOICES, method='get_is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user  # type: ignore
        if user.is_authenticated and value:
            return Recipe.objects.filter(favorites__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user  # type: ignore
        if user.is_authenticated and value:
            return Recipe.objects.filter(shopping_carts__user=user)
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )
