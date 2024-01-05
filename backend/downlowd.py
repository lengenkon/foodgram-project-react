# from backend.users.serializers import CustomUserSerializer
from django.contrib.auth import get_user_model
import os

import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()
from recipes.models import Tag, Ingredient, Recipe, Follow, IngredientIndividual, RecipeTag, Favorites, ShoppingList

# from django.core.asgi import get_asgi_application


User = get_user_model()

u = User.objects.get(id=1)


recipes_in_shopping_list = u.recipes_in_shopping_list.all()
shop_list = ShoppingList.objects.filter(user__id=1)
#  Первый вариант чз Шопинг лист
for i in shop_list:
    print(f'Для блюда {i.recipe} понадобится:')
    ingridients = IngredientIndividual.objects.filter(recipe=i.recipe)
    for i in ingridients:
        print(f'{i.ingredient.name} - {i.amount} {i.ingredient.measurement_unit}')
# Второй чз релейтед нейм у юзера и рецепта
for recipe in recipes_in_shopping_list:
    print(f'Для блюда {recipe.name} понадобится:')
    ingridients = IngredientIndividual.objects.filter(recipe=recipe)
    for i in ingridients:
        print(f'{i.ingredient.name} - {i.amount} {i.ingredient.measurement_unit}')

sourceFile = open('demo.txt', 'w')
print('Hello, Python!', file=sourceFile)
sourceFile.close()