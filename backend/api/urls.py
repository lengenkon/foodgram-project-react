from posixpath import relpath
from django.urls import include, path
from rest_framework import routers


from api.v1.views import (
    FollowViewSet, RecipeViewSet, TagViewSet, 
    CustomUserViewSet, IngredientViewSet
)


router_v1 = routers.DefaultRouter()
router_v1.register(r'users', CustomUserViewSet)
router_v1.register(r'recipes', RecipeViewSet)
# router_v1.register(r'recipes/(?P<recipes_id>\d+)/shopping_cart', ShoppingListViewSet.as_view({'get': 'post'}), basename='shoppinglist_create')
# router_v1.register(r'recipes/(?P<recipes_id>\d+)/shopping_cart', ShoppingListApiView.as_view(), basename='shoppinglist')
router_v1.register('ingredients', IngredientViewSet)
router_v1.register('tags', TagViewSet)
router_v1.register('follow', FollowViewSet, basename='follow')
# router_v1.register(
#     'titles',
#     TitleViewSet,
#     basename='titles',
# )
# router_v1.register(
#     'categories',
#     CategoryViewSet,
#     basename='categories',
# )
# router_v1.register(
#     'genres',
#     GenreViewSet,
#     basename='genres',
# )
# router_v1.register(
#     'users',
#     UsersViewSet,
#     basename='users',
# )
# router_v1.register(
#     r'titles/(?P<title_id>\d+)/reviews',
#     ReviewViewSet,
#     basename='reviews',
# )
# router_v1.register(
#     r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
#     CommentViewSet,
#     basename='comments',
# )


urlpatterns = [
    path(
        '',
        include(router_v1.urls),
    ),
    # path('recipes/<int:pk>/shopping_cart/', ShoppingListApiView.as_view(), name='shoppinglist'),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    # Djoser создаст набор необходимых эндпоинтов.
    # базовые, для управления пользователями в Django:
]
