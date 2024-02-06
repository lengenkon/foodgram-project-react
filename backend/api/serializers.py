import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from recipes.models import (Favorites, Ingredient, IngredientIndividual,
                            Recipe, ShoppingList, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import Follow

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from rest_framework import serializers
from users.models import Follow

User = get_user_model()

class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        if self.context['request'].user.is_authenticated:
            current_user = User.objects.get(
                username=self.context['request'].user)
            return Follow.objects.filter(
                following=obj.id, user=current_user.id).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'name',
            'slug',
            'color'
        )
        model = Tag


class IngredientSerilizer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientIndividualSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='ingredient.name')
    measurement_unit = serializers.CharField(
        read_only=True, source='ingredient.measurement_unit')
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = IngredientIndividual
        fields = ('id', 'amount', 'name', 'measurement_unit')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientIndividualSerializer(
        many=True,
        source='ingredientindividual_set')
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time',
                  'text', 'ingredients', 'tags', 'author',
                  'is_favorited', 'is_in_shopping_cart'
                  )
        model = Recipe

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_authenticated:
            current_user = User.objects.get(
                username=self.context.get('request').user)
            return Favorites.objects.filter(
                recipe=obj.id, user=current_user.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_authenticated:
            current_user = User.objects.get(
                username=self.context.get('request').user)
            return ShoppingList.objects.filter(
                recipe=obj.id, user=current_user.id).exists()
        return False

    def validate(self, data):
        data['tags'] = self.context['request'].data.get('tags', None)
        if not data['text']:
            raise serializers.ValidationError('Текст не может быть пустым!')
        if 'tags' not in data or 'ingredientindividual_set' not in data:
            raise serializers.ValidationError(['Заполните обязательное поле!'])
        if not data.get('tags'):
            raise serializers.ValidationError(
                {'tags': ['Не должно быть пустым!']})
        instance_list = []
        for element in data.get('tags'):
            try:
                instance = Tag.objects.get(id=element)
            except Tag.DoesNotExist:
                raise serializers.ValidationError(
                    {'tags': 'Нет такого тэга!'})
            if instance in instance_list:
                raise serializers.ValidationError(
                    {'tags': 'Уже добавлен в этот рецепт!'})
            instance_list.append(instance)
        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(['Не должно быть пустым!'])
        instance_list = []
        for element in ingredients:
            try:
                instance = Ingredient.objects.get(
                    id=element.get('ingredient').get('id'))
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    ['Нет такого ингредиента!'])
            if instance in instance_list:
                raise serializers.ValidationError(
                    ['Уже добавлен в этот рецепт!'])
            if int(element.get('amount')) <= 0:
                raise serializers.ValidationError(
                    {'amount': ['Количество должно быть больше 0']})
            instance_list.append(instance)
        return ingredients

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredientindividual_set')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        amount = [int(element['amount']) for element in ingredients]
        ingredient = [
            Ingredient.objects.get(
                id=int(element['ingredient']['id'])) for element in ingredients
        ]
        objects_of_model = []
        for i in range(len(ingredients)):
            object_dict = {
                'recipe': recipe,
                'ingredient': ingredient[i],
                'amount': amount[i]
            }
            objects_of_model.append(IngredientIndividual(**object_dict))
        IngredientIndividual.objects.bulk_create(objects_of_model)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredientindividual_set')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        amount = [int(element['amount']) for element in ingredients]
        ingredient = [
            Ingredient.objects.get(
                id=int(element['ingredient']['id'])) for element in ingredients
        ]
        objects_of_model = []
        for i in range(len(ingredients)):
            object_dict = {
                'recipe': instance,
                'ingredient': ingredient[i],
                'amount': amount[i]
            }
            objects_of_model.append(IngredientIndividual(**object_dict))
        IngredientIndividual.objects.bulk_create(objects_of_model)
        instance.save()
        return instance


class RecipeSerializer(RecipeGetSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CurrentFollowDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return User.objects.get(pk=serializer_field.context['pk'])


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    following = serializers.HiddenField(default=CurrentFollowDefault())
    email = serializers.CharField(read_only=True, source='following.email')
    id = serializers.IntegerField(read_only=True, source='following.id')
    username = serializers.CharField(
        read_only=True, source='following.username')
    first_name = serializers.CharField(
        read_only=True, source='following.first_name')
    last_name = serializers.CharField(
        read_only=True, source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField('paginated_recipes')
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'recipes',
            'recipes_count', 'user', 'following'
        )

    def paginated_recipes(self, obj):
        recipes = Recipe.objects.filter(
            author=obj.following).order_by('-created_at')
        page_size = self.context['request'].query_params.get(
            'recipes_limit') or 10
        paginator = Paginator(recipes, page_size)
        recipe_following = paginator.page(1)
        serializer = RecipeSerializer(recipe_following, many=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.following).count()

    def validate(self, data):
        if self.context['request'].user == data['following']:
            raise serializers.ValidationError(
                'Не может быть подписан сам на себя!')
        if Follow.objects.filter(user=data['user'],
                                 following=data['following']).exists():
            raise serializers.ValidationError(
                'Уже подписан!')
        return data


class CurrentRecipeDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return Recipe.objects.get(pk=serializer_field.context['pk'])


class ShoppingListSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.HiddenField(default=CurrentRecipeDefault())
    name = serializers.CharField(read_only=True, source='recipe.name')
    cooking_time = serializers.IntegerField(
        read_only=True, source='recipe.cooking_time')
    image = serializers.CharField(read_only=True, source='recipe.image')
    id = serializers.IntegerField(read_only=True, source='recipe.id')

    class Meta:
        model = ShoppingList
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message=('Рецепт уже добавлен')
            )
        ]


class FavoritesSerializer(ShoppingListSerializer):

    class Meta(ShoppingListSerializer.Meta):
        model = Favorites
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=('user', 'recipe'),
                message=('Рецепт уже добавлен')
            )
        ]
