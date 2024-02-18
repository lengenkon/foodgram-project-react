from itertools import chain

from django.contrib import admin
from users.models import Follow

from .models import (Favorites, Ingredient, IngredientIndividual, Recipe,
                     ShoppingList, Tag)


class IngredientIndividualInline(admin.TabularInline):
    def measurement_unit(self, obj):
        return self.model.ingredient.measurement_unit

    model = IngredientIndividual
    fields = ['ingredient', 'amount', 'measurement_unit']
    readonly_fields = ('measurement_unit',)
    extra = 1
    min_num = 1


class FollowAdmin(admin.ModelAdmin):
    empty_value_display = "-Нет-"
    list_display = (
        'user',
        'following'
    )
    search_fields = ('following',)


class IngredientAdmin(admin.ModelAdmin):
    list_filter = ('name', )
    list_display = (
        'name', 'measurement_unit', 'id'
    )


class IngredientIndividualAdmin(admin.ModelAdmin):
    def measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    list_display = (
        'recipe', 'ingredient',
        'amount', 'measurement_unit',
        'id'
    )


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'ingredient_for_recipe',
        'id', 'number_of_favorites', 'created_at'
    )
    list_filter = ('name', 'author', 'tags')
    inlines = (IngredientIndividualInline, )

    def ingredient_for_recipe(self, obj):
        ingredients = obj.ingredients.values_list('name')
        return list(chain.from_iterable(ingredients))

    def number_of_favorites(self, obj):
        count = Favorites.objects.filter(recipe=obj).count()
        return count


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'id', 'color', 'slug'
    )


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = (
        'recipe', 'id', 'user'
    )


class FavoritesAdmin(admin.ModelAdmin):
    list_display = (
        'recipe', 'id', 'user'
    )


class RecipeTagAdmin(admin.ModelAdmin):

    list_display = (
        'recipe', 'tag',
    )


admin.site.register(Follow, FollowAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientIndividual, IngredientIndividualAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)
admin.site.register(Favorites, FavoritesAdmin)
