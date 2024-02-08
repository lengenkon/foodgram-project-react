from django.urls import include, path
from rest_framework import routers

from .views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet)

router_v1 = routers.DefaultRouter()
router_v1.register('users', CustomUserViewSet)
router_v1.register(r'recipes', RecipeViewSet)
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet)


urlpatterns = [
    path(
        '',
        include(router_v1.urls),
    ),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
