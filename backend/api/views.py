from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from recipes.models import (
    Recipe, Tag, Follow, Ingredient,
    IngredientIndividual, ShoppingList, Favorites)
from rest_framework.response import Response
from .permissions import OwnerOrReadOnly, OwnerOnly
from .serializers import (
    RecipeCreateSerializer, RecipeGetSerializer, TagSerializer,
    FollowCreateSerializer, ShoppingListSerializer, FavoritesSerializer,
    IngredientSerilizer
)
from django.http import FileResponse
from .filters import RecipeFilter
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from users.serializers import CustomUserSerializer
from django.contrib.auth import get_user_model
# from rest_framework.generics import get_object_or_404
from rest_framework.status import (
    HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT, HTTP_201_CREATED)
from rest_framework.decorators import action


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if (self.action == 'me') and (
            self.request.user.is_authenticated is False
        ):
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
        following = get_object_or_404(User, pk=id)
        serializer = FollowCreateSerializer(
            data={"user": request.user, "following": following},
            context={'request': request, 'pk': id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=HTTP_201_CREATED, data=serializer.data)

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id=None):
        get_object_or_404(User, pk=id)
        if Follow.objects.filter(user=request.user.id, following=id).exists():
            instance = Follow.objects.get(user=request.user.id, following=id)
            instance.delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Пользователь не подписан'},
            status=HTTP_400_BAD_REQUEST)

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
        following = Follow.objects.select_related('following').filter(
            user=self.request.user)
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = FollowCreateSerializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = FollowCreateSerializer(
            following, many=True, context={'request': request})
        return Response(
            serializer.data,
        )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeGetSerializer
    permission_classes = (OwnerOrReadOnly, )
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    # def get_serializer_class(self):
    #     if self.action == 'list' or self.action == 'retrieve':
    #         return RecipeGetSerializer
    #     return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
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
    def shopping_cart(self, request, pk=None):
        if Recipe.objects.filter(pk=pk).exists():
            recipe = Recipe.objects.get(pk=pk)
            serializer = ShoppingListSerializer(
                data={"user": request.user, "recipe": recipe},
                context={'request': request, 'pk': pk})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=HTTP_201_CREATED, data=serializer.data)
        return Response(status=HTTP_400_BAD_REQUEST,
                        data={"errors": "Такого рецепта не существует"})

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            pk=pk)
        if ShoppingList.objects.filter(
            recipe=recipe, user=request.user
        ).exists():
            instance = ShoppingList.objects.get(
                recipe=recipe, user=request.user)
            instance.delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST,
                        data={"errors": "Такого рецепта нет в списке покупок"})

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
        if Recipe.objects.filter(pk=pk).exists():
            recipe = Recipe.objects.get(pk=pk)
            serializer = FavoritesSerializer(
                data={"user": request.user, "recipe": recipe},
                context={'request': request, 'pk': pk})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=HTTP_201_CREATED, data=serializer.data)
        else:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data={"errors": "Такого рецепта не существует"})

    @favorite.mapping.delete
    def favorite_delete(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            pk=pk)
        if Favorites.objects.filter(recipe=recipe, user=request.user).exists():
            # recipe = Recipe.objects.get(pk=pk)
            instance = Favorites.objects.get(recipe=recipe, user=request.user)
            instance.delete()
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
        # print(os.path.abspath('.'))

        # file_path = "{}data.txt".format(STATIC_URL)
        # with open(file_path, 'w', encoding='utf-8') as file:
        filename = 'test.txt'
        filepath = 'static/data/' + filename
        sourceFile = open(filepath, 'w', encoding='utf-8')
        recipes_in_shopping_list = request.user.recipes_in_shopping_list.all()
        for recipe in recipes_in_shopping_list:
            print(f'Для блюда "{recipe.name}" понадобится:', file=sourceFile)
            ingridients = IngredientIndividual.objects.filter(recipe=recipe)
            for i in ingridients:
                print(
                    f'{i.ingredient.name} - {i.amount} '
                    f'{i.ingredient.measurement_unit}',
                    file=sourceFile)
        sourceFile.close()
        return FileResponse(open(filepath, 'rb'))


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class FollowViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                    viewsets.GenericViewSet):
    # НИГДЕ НЕ ИСПОЛЬЗУЕТСЯ
    pagination_class = LimitOffsetPagination
    # serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.SearchFilter, )
    search_fields = ('following__username',)

    def get_queryset(self):
        return Follow.objects.select_related('following').filter(
            user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    # queryset = Ingredient.objects.all()
    serializer_class = IngredientSerilizer
    filter_backends = (filters.SearchFilter, )
    # не работает
    # search_fields = ('name', )
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__istartswith=name)
        return queryset
