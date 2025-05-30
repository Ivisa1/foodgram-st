from django_filters import rest_framework as rest_framework_filters
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import (
    F,
    Sum
)
from django.http import FileResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend

from djoser.views import UserViewSet

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)

from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from recipes.models import (
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    RecipeIngredient
)
from .serializers import (
    IngredientSerializer,
    ReadRecipeSerializer,
    CreateRecipeSerializer,
    ShortRecipeSerializer,
    UserRecipesSerializer
)

from .filters import (
    IngredientFilter,
    RecipeFilter
)
from .permissions import IsAuthorOrReadOnly

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингридиентами"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (rest_framework_filters.DjangoFilterBackend, )
    filterset_class = IngredientFilter
    permission_classes = (AllowAny, )
    pagination_class = None


class UserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями"""

    lookup_url_kwarg = 'pk'

    @action(
        methods=('get', ),
        detail=False,
        url_path='me',
        url_name='me',
        permission_classes=(IsAuthenticated, ),
    )
    def me(self, request):
        """Функция для работы с текущим пользователем"""

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        methods=('put', 'delete'),
        detail=False,
        url_path='me/avatar',
        permission_classes=(IsAuthenticated, )
    )
    def avatar(self, request):
        """Функция для работы с аватаром пользователя"""

        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                raise ValidationError({'avatar': 'Обязательное поле.'})

            serializer = self.get_serializer(
                user,
                data={'avatar': request.data['avatar']},
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                {'avatar': serializer.data['avatar']},
                status=status.HTTP_200_OK
            )

        elif request.method == 'DELETE':
            if not user.avatar:
                return Response(
                    {'detail': 'Аватар уже отсутствует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.avatar.delete()
            user.avatar = ""
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('get', ),
        detail=False,
        url_path='subscriptions',
        url_name='subscriptions',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Функция для возврата подписок пользователя"""

        queryset = User.objects.filter(authors__subscriber=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = UserRecipesSerializer(
            pages, many=True, context={'request': request}
        )

        return self.get_paginated_response(serializer.data)

    @action(
        methods=('post', 'delete'),
        detail=True,
        url_path='subscribe',
        url_name='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, pk):
        """Функция для подписки/отписки"""

        user = request.user
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            obj, is_created = user.subscriptions.get_or_create(author=author)
            if not is_created:
                return Response(
                    {'detail': f'Вы уже подписаны на {author}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserRecipesSerializer(
                author, context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            obj = user.subscriptions.filter(author=author)
            if not obj.exists():
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами"""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReadRecipeSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        """Подтверждение записи рецепта в БД"""

        serializer.save(author=self.request.user)

    def check_in_fav_or_sc(self, model, request, recipe_id):
        """Добавление/удаление рецепта в
        избранное/корзину."""

        user = request.user
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if request.method == 'POST':
            obj, is_created = model.objects.get_or_create(
                user_id=user.id, recipe_id=recipe.id
            )
            if not is_created:
                return Response(
                    {'detail': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                ShortRecipeSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            deleted, _ = model.objects.filter(
                user=user, recipe=recipe
            ).delete()
            if deleted:
                return Response(
                    {'detail': 'Рецепт успешно удален из избранного'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response({'detail': 'Рецепт не найден в избранном'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=('post', 'delete'),
        detail=True,
        url_path='favorite',
        url_name='favorite',
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        """Добавление/удаление рецепта в(из) избранное(го)"""

        return self.check_in_fav_or_sc(Favorite, request, pk)

    @action(
        methods=('post', 'delete'),
        detail=True,
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(IsAuthenticated, ),
    )
    def shopping_cart(self, request, pk):
        """Добавление/удаление рецепта в(из) корзину(ы)"""

        return self.check_in_fav_or_sc(ShoppingCart, request, pk)

    def create_file_structure(self, user, recipes, ingredients):
        return '\n'.join([
            f"Список покупок пользователя {user}",
            "___________________________",
            "Список рецептов:",
            *(
                f"- {recipe.name}" for recipe in recipes),
            "",
            "Список ингредиентов:",
            *(f"{i}. {item['name']} — "
              f"{item['amount']} {item['unit']}"
              for i, item in enumerate(ingredients, 1))]
        )

    @action(
        methods=('get', ),
        detail=False,
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(IsAuthenticated, ),
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        ).annotate(amount=Sum('amount')).order_by('name')

        recipes = Recipe.objects.filter(
            shopping_carts__user=user
        ).select_related('author')

        content = self.create_file_structure(user, recipes, ingredients)

        return FileResponse(
            content,
            filename='shopping_list.txt',
            as_attachment=True,
            content_type='text/plain'
        )

    @action(
        methods=('get', ),
        detail=True,
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk):
        get_object_or_404(Recipe, pk=pk)
        url = reverse('recipes:get_recipe_link', args=(pk,))
        absolute_url = request.build_absolute_uri(url)
        return Response({
            'short-link': absolute_url
        })
