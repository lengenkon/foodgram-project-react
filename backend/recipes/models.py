from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

MAX_lENGHT_TAG = 32
MIN_VALUE = 1
MAX_VALUE_AMOUNT = 32000
MAX_VALUE_TIME = 32000
MAX_LENGHT_NAME = 64



User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_lENGHT_TAG,
        unique=True,
    )
    slug = models.SlugField(
        'Идентификатор',
        max_length=MAX_lENGHT_TAG,
        unique=True,
    )
    color = ColorField(default='#FF0000')

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('id', )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGHT_NAME,
    )
    measurement_unit = models.CharField(
        'Едиинца измерения',
        max_length=MAX_LENGHT_NAME,
        default='кг'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('id', )
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'name',
                    'measurement_unit',
                ],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return self.name


class IngredientIndividual(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(MIN_VALUE, message=f"Минимум - {MIN_VALUE} eдиница"),
                   MaxValueValidator(MAX_VALUE_TIME, message=f"Максимум - {MAX_VALUE_AMOUNT} единиц")]
    )

    class Meta:
        verbose_name = 'ингредиент определенного рецепта'
        verbose_name_plural = 'Ингредиенты определенного рецепта'
        ordering = ('id', )
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'ingredient',
                    'recipe',
                ],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'({self.ingredient.name} в рецепте {self.recipe.name})


class Recipe(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGHT_NAME_RECIPE,
    )
    text = models.TextField(
        'Описание',
        max_length=MAX_LENGHT_TEXT,
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(MIN_VALUE, message=f"Минимум - {MIN_VALUE} минута"),
                   MaxValueValidator(MAX_VALUE_TIME, message=f"Максимум - {MAX_VALUE_TIME} минут")]
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/', null=True, blank=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes'
    )
    created_at = models.DateTimeField(
        'Дата и время создания',
        auto_now_add=True,
    )
    tags = models.ManyToManyField(
        Tag, related_name='tags')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientIndividual', related_name='ingredients')
    is_favorited = models.ManyToManyField(
        User, through='Favorites', related_name='favorites_recipes')
    is_shopping_list = models.ManyToManyField(
        User, through='ShoppingList', related_name='recipes_in_shopping_list')

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at', )

    def __str__(self):
        return self.name

class BaseUserRecipe(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
    )

class Favorites(BaseUserRecipe):
    
    class Meta:
        default_related_name = 
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('id', )


class ShoppingList(BaseUserRecipe):
    
    class Meta:
        default_related_name = 
        verbose_name = 'список покупок'
        verbose_name_plural = 'Cписок покупок'
        ordering = ('id', )
