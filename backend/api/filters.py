from django_filters.rest_framework import CharFilter, FilterSet, BooleanFilter


from recipes.models import Recipe


class RecipeFilter(FilterSet):
    """Фильтр преобразовывает поля жанра и категории."""

    tags = CharFilter(field_name='tags__slug')
    cooking_time = CharFilter(method='my_custom_filter')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    is_favorited = BooleanFilter(method='filter_is_favorited')

    # = CharFilter(field_name='category__slug')

    class Meta:
        model = Recipe
        fields = (
            'author', 'is_in_shopping_cart', 'cooking_time', 'is_favorited'
        )

    def my_custom_filter(self, queryset, name, value):
        return queryset.filter(**{
            name: value,
        })

    def filter_is_in_shopping_cart(self, queryset, value, name):
        if value and name == 1 and self.request.user.is_authenticated:
            return self.request.user.recipes_in_shopping_list.all()
        return queryset
    
    def filter_is_favorited(self, queryset, value, name):
        if value and name == 1 and self.request.user.is_authenticated:
            return self.request.user.favorites_recipes.all()
        return queryset

# class ShoppingCartFilter(FilterSet):
#     is_shopping_cart = BooleanFilter(field_name='recipe__id') method='is_shopping', field_name=)
    
#     def is_shopping(self, queryset, field_name, value, ):
#         if value == 0:
#             shopping_cart = ShoppingList.objects.filter(recipe=)


#     class Meta:
#         model = ShoppingList
#         fields = ('is_shopping_cart', )
