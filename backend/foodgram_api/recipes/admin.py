from django.contrib import admin

from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)


class BaseAdmin(admin.ModelAdmin):
    """Базовый класс"""
    
    readonly_fields = ('id', )


@admin.register(Ingredient)
class IngredientAdmin(BaseAdmin):
    """Класс для ингридиентов"""

    list_display = ('name', 'id', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ('name',)
    fields = ('name', 'id', 'measurement_unit')  # Показываем ID при редактировании


class RecipeIngredientInline(admin.TabularInline):
    """Класс для редактирования связей"""
    model = Recipe.ingredients.through
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(BaseAdmin):
    """Класс для рецептов"""

    list_display = ('name', 'id', 'author', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('name', 'author')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('id', 'favorites_count', 'pub_date')
    
    fieldsets = (
        (None, {'fields': ('name', 'id', 'author', 'pub_date')}),
        ('Content', {'fields': ('image', 'text', 'cooking_time')}),
        ('Statistics', {'fields': ('favorites_count',)}),
    )
    
    def favorites_count(self, obj):
        return obj.favorites.count()
    favorites_count.short_description = 'Добавлений в избранное'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(BaseAdmin):
    """Класс для связи рецепт-ингридиенты"""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    fields = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(BaseAdmin):
    """Класс для редактирования избранного"""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    fields = ('id', 'user', 'recipe')

@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseAdmin):
    """Класс для редактирования корзины"""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    fields = ('id', 'user', 'recipe')
