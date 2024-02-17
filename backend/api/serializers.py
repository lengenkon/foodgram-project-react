from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorites, Ingredient, IngredientIndividual,
                            Recipe, ShoppingList, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import Follow

from .utils import get_field

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        return get_field(self, obj, Follow, 'following')


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

    def validate(self, data):
        try:
            Ingredient.objects.get(
                id=data.get('id'))
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                ['Нет такого ингредиента!'])
        return data


class IngredientIndividualSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='ingredient.name')
    measurement_unit = serializers.CharField(
        read_only=True, source='ingredient.measurement_unit')
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = IngredientIndividual
        fields = ('id', 'amount', 'name', 'measurement_unit')


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientIndividualSerializer(
        many=True,
        source='ingredientindividual_set',
    )
    image = Base64ImageField(required=True)

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time',
                  'text', 'ingredients', 'tags', 'author',
                  'is_favorited', 'is_in_shopping_cart'
                  )
        model = Recipe

    def get_is_favorited(self, obj):
        return get_field(self, obj, Favorites, 'recipe')

    def get_is_in_shopping_cart(self, obj):
        return get_field(self, obj, ShoppingList, 'recipe')


class RecipeSerializerCreate(RecipeGetSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault())

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time',
                  'text', 'ingredients', 'tags', 'author',
                  'is_favorited', 'is_in_shopping_cart'
                  )
        model = Recipe

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(['Не должно быть пустым!'])
        return value

    def validate(self, data):
        if not data.get('tags'):
            raise serializers.ValidationError(
                {'tags': ['Не должно быть пустым!']})
        instance_list = []
        for element in data.get('tags'):
            if element in instance_list:
                raise serializers.ValidationError(
                    {'tags': 'Уже добавлен в этот рецепт!'})
            instance_list.append(element)
        if not data.get('ingredientindividual_set'):
            raise serializers.ValidationError(
                {'ingredients': ['Не должно быть пустым!']})
        instance_list = []
        for element in data.get('ingredientindividual_set'):
            try:
                instance = Ingredient.objects.get(
                    id=element.get('ingredient').get('id'))
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    ['Нет такого ингредиента!'])
            if instance in instance_list:
                raise serializers.ValidationError(
                    ['Уже добавлен в этот рецепт!'])
            instance_list.append(instance)
        return data

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

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(
            instance, context={'request': self.context['request']})
        return serializer.data


class RecipeSerializer(RecipeGetSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializerCreate(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = (
            'user', 'following'
        )

    def validate(self, data):
        if self.context['request'].user == data['following']:
            raise serializers.ValidationError(
                'Не может быть подписан сам на себя!')
        if Follow.objects.filter(user=data['user'],
                                 following=data['following']).exists():
            raise serializers.ValidationError(
                'Уже подписан!')
        return data

    def to_representation(self, instance):
        serializer = FollowSerializer(
            instance.following,
            context={'request': self.context['request']})
        return serializer.data


class FollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField('paginated_recipes')
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'recipes',
            'recipes_count',
        )

    def paginated_recipes(self, obj):
        page_size = self.context['request'].query_params.get(
            'recipes_limit') or 10
        recipes = Recipe.objects.filter(
            author=obj).order_by('-created_at')[:int(page_size)]
        serializer = RecipeSerializer(recipes, many=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class ShoppingListSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message=('Рецепт уже добавлен')

            )
        ]

    def to_representation(self, instance):
        serializer = RecipeUserSerializer(
            instance.recipe,
            context={'request': self.context['request']})
        return serializer.data


class RecipeUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoritesSerializer(ShoppingListSerializer):

    class Meta:
        model = Favorites
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message=('Рецепт уже добавлен')
            )
        ]
