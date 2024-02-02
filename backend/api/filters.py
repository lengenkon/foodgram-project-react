from django_filters.rest_framework import (
    FilterSet, BooleanFilter, AllValuesMultipleFilter)
from recipes.models import Recipe


class RecipeFilter(FilterSet):

    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    is_favorited = BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = (
            'author', 'is_in_shopping_cart', 'tags', 'is_favorited'
        )

    def filter_is_in_shopping_cart(self, queryset, value, name):
        if value and name == 1 and self.request.user.is_authenticated:
            return self.request.user.recipes_in_shopping_list.all()
        return queryset

    def filter_is_favorited(self, queryset, value, name):
        if value and name == 1 and self.request.user.is_authenticated:
            return self.request.user.favorites_recipes.all()
        return queryset
