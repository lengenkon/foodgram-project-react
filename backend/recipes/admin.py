from django.contrib import admin
from .models import (
    Follow, Ingredient, Tag, Recipe,
    IngredientIndividual, ShoppingList, RecipeTag)
from django.contrib.auth import get_user_model
from itertools import chain

User = get_user_model()


class IngredientIndividualInline(admin.TabularInline):
    model = IngredientIndividual
    extra = 1


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag
    extra = 1


class FollowAdmin(admin.ModelAdmin):
    empty_value_display = "-Нет-"
    list_display = (
        'user',
        'following'
    )
    search_fields = ('following',)
    # list_display_links = ('user',)


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'last_name', 'id'
    )


class IngredientAdmin(admin.ModelAdmin):
    inlines = (IngredientIndividualInline,)
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
    inlines = (IngredientIndividualInline, RecipeTagInline)

    def ingredient_for_recipe(self, obj):
        a = obj.ingredients.values_list('name')
        return list(chain.from_iterable(a))

    list_display = (
        'name', 'author', 'ingredient_for_recipe', 'id'
    )


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'id', 'color', 'slug'
    )


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = (
        'recipe', 'id', 'user'
    )


class RecipeTagAdmin(admin.ModelAdmin):

    list_display = (
        'recipe', 'tag',
    )


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientIndividual, IngredientIndividualAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeTag, RecipeTagAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)
