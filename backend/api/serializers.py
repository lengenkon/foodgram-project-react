import base64
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator
from django.core.files.base import ContentFile

from recipes.models import Tag, Ingredient, Recipe, Follow, IngredientIndividual, RecipeTag, Favorites, ShoppingList
from users.serializers import CustomUserSerializer


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'name',
            'slug',
            'color'
        )
        model = Tag


class IngredientSerilizer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientIndividualGetSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='ingredient.name')
    measurement_unit = serializers.CharField(read_only=True, source='ingredient.measurement_unit')

    class Meta:
        model = IngredientIndividual
        fields = ('id', 'amount', 'name', 'measurement_unit')


class IngredientIndividualCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = IngredientIndividual
        fields = ('id', 'amount')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientIndividualCreateSerializer(many=True, 
                                                 read_only=True,
                                                 source='ingredientindividual_set')

    class Meta:
        fields = (
            'name', 'image', 'cooking_time', 'text',
            'ingredients',
            'tags'
        )
        model = Recipe

    def create(self, validated_data):
        tags = self.initial_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            current_tag = Tag.objects.get(pk=tag)
            RecipeTag.objects.create(recipe=recipe, tag=current_tag)
        ingredients = self.initial_data.get('ingredients')
        for ingredient in ingredients:
            amount = ingredient.pop('amount')
            current_ingredient = Ingredient.objects.get(**ingredient)
            IngredientIndividual.objects.create(
                ingredient=current_ingredient, recipe=recipe, amount=amount)
        return recipe

    def update(self, instance, validated_data):
        print(instance)
        instance.name = validated_data.get("name", instance.name)
        instance.cooking_time = validated_data.get("cooking_time", instance.cooking_time)
        instance.text = validated_data.get("text", instance.text)
        instance.image = validated_data.get("image", instance.image)
        instance.save()
        if 'tags' in self.initial_data:
            tags = self.initial_data.pop('tags')
            for tag in tags:
                current_tag = Tag.objects.get(pk=tag)
                RecipeTag.objects.get_or_create(recipe=instance, tag=current_tag)
        if 'ingredients' in self.initial_data:
            ingredients = self.initial_data.get('ingredients')
            for ingredient in ingredients:
                amount = ingredient.pop('amount')
                current_ingredient = Ingredient.objects.get(**ingredient)
                IngredientIndividual.objects.get_or_create(
                    ingredient=current_ingredient, recipe=instance, amount=amount)
        return instance


class RecipeGetSerializer(RecipeCreateSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientIndividualGetSerializer(many=True, 
                                                 read_only=True,
                                                 source='ingredientindividual_set')
    
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time', 'text', 'ingredients', 'tags', 'author',
                  'is_favorited', 'is_in_shopping_cart'
                  )
        model = Recipe

    def get_is_favorited(self, obj):
        current_user = User.objects.get(username=self.context.get('request').user)
        return Favorites.objects.filter(
            recipe=obj.id, user=current_user.id).exists()
    
    def get_is_in_shopping_cart(self, obj):
        current_user = User.objects.get(username=self.context.get('request').user)
        return ShoppingList.objects.filter(
            recipe=obj.id, user=current_user.id).exists()
    

class RecipeSerializer(RecipeGetSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowCreateSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('following', 'user')
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message=('Вы уже подписаны на данного пользователя')
            )
        ]

    def validate(self, data):
        if self.context['request'].user == data['following']:
            raise serializers.ValidationError(
                'Не может быть подписан сам на себя!')
        return data


class FollowSerializer(serializers.ModelSerializer):

    email = serializers.CharField(source='following.email')
    username = serializers.CharField(source='following.username')
    first_name = serializers.CharField(source='following.first_name')
    last_name = serializers.CharField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSerializer(many=True, source='following.recipes')
    recipes_count = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        current_user = User.objects.get(username=self.context.get('request').user)
        return Follow.objects.filter(
            following=obj.following_id, user=current_user.id).exists()
    
    def get_recipes_count(self, obj):
        # Получить количество рецептов пользователя
        return Recipe.objects.filter(author=obj.following_id).count()

    class Meta:
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count'
        )
        model = Follow


class CurrentRecipeDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return Recipe.objects.get(pk=serializer_field.context['pk'])


class ShoppingListSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.HiddenField(default=CurrentRecipeDefault())
    name = serializers.CharField(read_only=True, source='recipe.name')
    cooking_time = serializers.CharField(
        read_only=True, source='recipe.cooking_time')
    image = serializers.CharField(read_only=True, source='recipe.image')
    id = serializers.CharField(read_only=True, source='recipe.id')


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
        # fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=('user', 'recipe'),
                message=('Рецепт уже добавлен')
            )
        ]
