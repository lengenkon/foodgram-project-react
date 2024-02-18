from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorites, Ingredient, IngredientIndividual,
                            Recipe, ShoppingList, Tag)
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .pagination import PaginationWithLimit
from .permissions import OwnerOnly, OwnerOrReadOnly
from .serializers import (CustomUserSerializer, FavoritesSerializer,
                          FollowSerializer, FollowSerializerCreate,
                          IngredientSerilizer, RecipeGetSerializer,
                          RecipeSerializerCreate, ShoppingListSerializer,
                          TagSerializer)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = PaginationWithLimit

    def get_permissions(self):
        if self.action == 'me':
            return (OwnerOnly(), )
        return super().get_permissions()

    @action(
        methods=[
            'post'
        ],
        permission_classes=(
            IsAuthenticated,
        ),
        detail=True,
    )
    def subscribe(self, request, id=None):
        get_object_or_404(User, id=id)
        serializer = FollowSerializerCreate(
            data={"user": request.user.id, "following": id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=HTTP_201_CREATED, data=serializer.data)

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id=None):
        get_object_or_404(User, id=id)
        if not Follow.objects.filter(
            user=request.user.id,
            following=id
        ).delete()[0]:
            return Response(
                {'errors': 'Пользователь не подписан'},
                status=HTTP_400_BAD_REQUEST)
        return Response(status=HTTP_204_NO_CONTENT)

    @action(
        methods=[
            'get'
        ],
        permission_classes=(
            IsAuthenticated,
        ),
        url_path='subscriptions',
        detail=False,
    )
    def subscriptions(self, request):
        following = User.objects.filter(followers__user=request.user)
        page = self.paginate_queryset(following)
        serializer = FollowSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related(
        'author').prefetch_related(
            'tags',
            'ingredients').order_by('-created_at')
    pagination_class = PaginationWithLimit
    permission_classes = (OwnerOrReadOnly, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrive':
            return RecipeGetSerializer
        return RecipeSerializerCreate

    @action(
        methods=[
            'post'
        ],
        permission_classes=(
            IsAuthenticated,
        ),
        detail=True,
    )
    def shopping_cart(self, request, pk=None):
        serializer = ShoppingListSerializer(
            data={"user": request.user.id, "recipe": pk},
            context={'request': request, 'pk': pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=HTTP_201_CREATED, data=serializer.data)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            pk=pk)
        if ShoppingList.objects.filter(
            recipe=recipe, user=request.user
        ).delete()[0]:
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(
            status=HTTP_400_BAD_REQUEST,
            data={"errors": "Такого рецепта нет в списке покупок"}
        )

    @action(
        methods=[
            'post'
        ],
        permission_classes=(
            IsAuthenticated,
        ),
        detail=True,
    )
    def favorite(self, request, pk=None):
        serializer = FavoritesSerializer(
            data={"user": request.user.id, "recipe": pk},
            context={'request': request, 'pk': pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=HTTP_201_CREATED, data=serializer.data)

    @favorite.mapping.delete
    def favorite_delete(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            pk=pk)
        if Favorites.objects.filter(
            recipe=recipe,
            user=request.user
        ).delete()[0]:
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST,
                        data={"errors": "Такого рецепта нет в избранном"})

    @action(
        methods=[
            'get'
        ],
        permission_classes=(
            IsAuthenticated,
        ),
        detail=False,
    )
    def download_shopping_cart(self, request):
        filename = 'test.txt'
        filepath = 'static/data/' + filename
        sourceFile = open(filepath, 'w', encoding='utf-8')
        recipes_in_shopping_list = Recipe.objects.filter(
            shoppinglist__user=self.request.user)
        for recipe in recipes_in_shopping_list:
            sourceFile.write(f'Для блюда "{recipe.name}" понадобится:\n')
            ingridients = IngredientIndividual.objects.filter(recipe=recipe)
            for i in ingridients:
                sourceFile.write(
                    f'{i.ingredient.name} - {i.amount} '
                    f'{i.ingredient.measurement_unit}\n'
                )
        sourceFile.close()
        return FileResponse(open(filepath, 'rb'))


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerilizer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
