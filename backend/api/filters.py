from django_filters.rest_framework import (AllValuesMultipleFilter,
                                           BooleanFilter, FilterSet)
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
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                is_shopping_list=self.request.user).order_by(
                '-created_at')
        return queryset

    def filter_is_favorited(self, queryset, value, name):
        if value and self.request.user.is_authenticated:
            return queryset.filter(is_favorited=self.request.user).order_by(
                '-created_at')
        return queryset
