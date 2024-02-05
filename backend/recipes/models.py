from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=32,
    )
    slug = models.SlugField(
        'Идентификатор',
        max_length=32,
        unique=True,
    )
    color = ColorField(default='#FF0000')

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=64,
    )
    measurement_unit = models.CharField(
        'Едиинца измерения',
        max_length=32,
        default='кг'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class IngredientIndividual(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    amount = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1, message="Минимум - 1 единица")]
    )

    class Meta:
        verbose_name = 'ингредиент определенного рецепта'
        verbose_name_plural = 'Ингредиенты определенного рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'ingredient',
                    'recipe',
                ],
                name='unique_recipe_ingredient'
            )
        ]


class Recipe(models.Model):
    name = models.CharField(
        'Название',
        max_length=200,
    )
    text = models.TextField(
        'Описание',
        max_length=1024,
    )
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1, message="Минимум - 1 минута")]
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

    def __str__(self):
        return self.name


class Favorites(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Cписок покупок'
