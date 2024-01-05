from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from recipes.models import Recipe, Tag, Follow, Ingredient, IngredientIndividual, ShoppingList, Favorites
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .permissions import OwnerOrReadOnly
from .serializers import (
    FollowSerializer, RecipeCreateSerializer, RecipeGetSerializer, TagSerializer, 
    FollowCreateSerializer, ShoppingListSerializer, FavoritesSerializer, 
    IngredientSerilizer
)
import mimetypes
from backend.settings import STATIC_URL, BASE_DIR, STATICFILES_DIRS
from django.http import HttpResponse
from .filters import RecipeFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from djoser.views import UserViewSet
from users.serializers import CustomUserSerializer
from django.contrib.auth import get_user_model
from rest_framework.generics import get_object_or_404, GenericAPIView, DestroyAPIView
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT
from rest_framework.decorators import action


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = AllowAny

    @action(
        methods=[
            'post'
        ],
        permission_classes=(
            IsAuthenticated,
        ),
        url_path='subscribe',
        detail=True,
    )
    def subscribe(self, request, id=None):
        # user = request.user
        following = get_object_or_404(User, pk=id)
        serializer = FollowCreateSerializer(data={"user": request.user.id, "following": id},
                                            context={'request': request})
        print(serializer)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer_user = CustomUserSerializer(following, context={'request': request})
        print(serializer_user)
        return Response(serializer_user.data)
    
    @subscribe.mapping.delete
    def subscribe_delete(self, request, id=None):
        if Follow.objects.filter(user=request.user.id, following=id).exists():
            instance = Follow.objects.get(user=request.user.id, following=id)
            instance.delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response({'errors': 'Пользователь не подписан'}, status=HTTP_400_BAD_REQUEST)
        
    @action(
        methods=[
            'get'
        ],
        permission_classes=(
            IsAuthenticated,
        ),
        # url_path='subscriptions',
        detail=False,
    )
    def subscriptions(self, request):
        following = Follow.objects.select_related('following').filter(
            user=self.request.user)
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = FollowSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        print(following)
        serializer = FollowSerializer(following, many=True, context={'request': request})
        print(serializer.data)
        return Response(
            serializer.data,
        )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related('ingredients', 'is_shopping_list')
    permission_classes = (OwnerOrReadOnly, )
    pagination_class = LimitOffsetPagination
    # pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return RecipeGetSerializer
        return RecipeCreateSerializer

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
        # url_path='shopping_cart',
        detail=True,
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            pk=pk)
        serializer = ShoppingListSerializer(data={"user": request.user, "recipe": recipe},
                                            context={'request': request, 'pk': pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data) 

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            pk=pk)
        instance = ShoppingList.objects.get(recipe=recipe, user=request.user)
        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT) 
    
    @action(
        methods=[
            'post'
        ],
        permission_classes=(
            IsAuthenticated,
        ),
        # url_path='favorite',
        detail=True,
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            pk=pk)
        serializer = FavoritesSerializer(data={"user": request.user, "recipe": recipe}, 
                                         context={'request': request, 'pk': pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data) 

    @favorite.mapping.delete
    def favorite_delete(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            pk=pk)
        instance = Favorites.objects.get(recipe=recipe, user=request.user)
        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT) 
    
    @action(
        methods=[
            'get'
        ],
        permission_classes=(
            IsAuthenticated,
        ),
        # url_path='favorite',
        detail=False,
    )
    def download_shopping_cart(self, request):
        # file_path = "{}data.txt".format(STATIC_URL)
        # with open(file_path, 'w', encoding='utf-8') as file:
        filename = 'test.txt'
        filepath = 'backend/static/data/' + filename
        sourceFile = open(filepath, 'w', encoding='utf-8')
        recipes_in_shopping_list = request.user.recipes_in_shopping_list.all()
        for recipe in recipes_in_shopping_list:
            print(f'Для блюда {recipe.name} понадобится:', file=sourceFile)
            ingridients = IngredientIndividual.objects.filter(recipe=recipe)
            for i in ingridients:
                print(f'{i.ingredient.name} - {i.amount} {i.ingredient.measurement_unit}', file=sourceFile)
        mime_type, _ = mimetypes.guess_type(filepath)
        response = HttpResponse(sourceFile, content_type=mime_type)   
        sourceFile.close()
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
        # response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response

        filename = "demo.txt"
        content = 'any string generated by django'
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
        return response
        # return HttpResponse("Here's the text of the Web page.")
    
    


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class FollowViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                    viewsets.GenericViewSet):
    # НИГДЕ НЕ ИСПОЛЬЗУЕТСЯ
    pagination_class = LimitOffsetPagination
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.SearchFilter, )
    search_fields = ('following__username',)

    def get_queryset(self):
        return Follow.objects.select_related('following').filter(
            user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# class ShoppingListViewSet(viewsets.GenericViewSet):
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     queryset = ShoppingList.objects.all()
#     serializer_class = ShoppingListSerializer


# class ShoppingListApiView(APIView):

#     def delete(self, request, pk):
#         user = self.request.user
#         recipe = get_object_or_404(
#             Recipe,
#             pk=pk)
#         instance = ShoppingList.objects.get(recipe=recipe, user=user)
#         instance.delete()
#         return Response(status=HTTP_204_NO_CONTENT)
    
#     def post(self, request, pk):
#         recipe = get_object_or_404(
#             Recipe,
#             pk=pk)
#         serializer = ShoppingListSerializer(data={"user": request.user, "recipe": recipe},
#                                             context={'request': request, 'pk': pk})
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
    





# class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = IngredientIndividual.objects.all()
#     serializer_class = IngredientIndividualSerializer

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerilizer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name', ) 