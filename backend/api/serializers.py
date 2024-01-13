import base64
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator
from django.core.files.base import ContentFile
from .utils import validation_field, validation_field_ingredients, validation_field_tags
from django.core.paginator import Paginator

from recipes.models import Tag, Ingredient, Recipe, Follow, IngredientIndividual, RecipeTag, Favorites, ShoppingList
from users.serializers import CustomUserSerializer


User = get_user_model()


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


class IngredientIndividualGetSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='ingredient.name')
    measurement_unit = serializers.CharField(
        read_only=True, source='ingredient.measurement_unit')

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


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientIndividualGetSerializer(many=True,
                                                    read_only=True,
                                                    source='ingredientindividual_set')
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time', 'text', 'ingredients', 'tags', 'author',
                  'is_favorited', 'is_in_shopping_cart'
                  )
        model = Recipe
        extra_kwargs = {'text': {'required': True}}

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


class RecipeCreateSerializer(RecipeGetSerializer):
    # image = Base64ImageField(required=False, allow_null=True)
    # ingredients = IngredientIndividualGetSerializer(many=True,
    #  read_only=True,
    #  source='ingredientindividual_set')
    # author = CustomUserSerializer(read_only=True)

    class Meta:
        fields = (
            'id', 'tags', 'author',
            'name', 'image', 'cooking_time', 'text',
            'ingredients',
            'is_favorited', 'is_in_shopping_cart'
        )
        model = Recipe
        extra_kwargs = {'text': {'required': True}}

    def validate(self, data):
        if not data['text']:
            raise serializers.ValidationError('Текст не может быть пустым!')
        return data

    def create(self, validated_data):
        recipe = Recipe.objects.create(**validated_data)
        # if self.initial_data.get('tags', False):
        #     tags = self.initial_data.get('tags')
        #     for tag in tags:
        #         if Tag.objects.filter(id=tag).exists():
        #             current_tag = Tag.objects.get(pk=tag)
        #             if RecipeTag.objects.filter(tag=current_tag, recipe=recipe).exists():
        #                 raise serializers.ValidationError(
        #                     {'tags': ['Этот tag уже добавлен в этот рецепт!']})
        #             RecipeTag.objects.create(recipe=recipe, tag=current_tag)
        #         else:
        #             raise serializers.ValidationError(
        #                 {'tags': 'Нет такого ингредиента!'})
        # else:
        #     raise serializers.ValidationError(
        #         {'tags': ['Не все поля заполнены!']})
        validation_field_ingredients(
            recipe=recipe,
            data=self.initial_data,
            field='ingredients',
            model=Ingredient,
            through_model=IngredientIndividual)
        validation_field_tags(
            recipe=recipe,
            data=self.initial_data,
            field='tags',
            model=Tag,
            through_model=RecipeTag)
        # if self.initial_data.get('ingredients', False):
        #     ingredients = self.initial_data.get('ingredients')
        #     for ingredient in ingredients:
        #         amount = ingredient.pop('amount')
        #         if Ingredient.objects.filter(**ingredient).exists():
        #             current_ingredient = Ingredient.objects.get(**ingredient)
        #             if IngredientIndividual.objects.filter(ingredient=current_ingredient, recipe=recipe).exists():
        #                 raise serializers.ValidationError(
        #                     {'ingredients': 'Этот ингредиент уже добавлен в этот рецепт!'})
        #             if amount >= 1:
        #                 IngredientIndividual.objects.create(
        #                     ingredient=current_ingredient, recipe=recipe, amount=amount)
        #             else:
        #                 raise serializers.ValidationError({'amount': ['Количество должно быть больше 1']})
        #         else:
        #             raise serializers.ValidationError(
        #                 {'ingredients': 'Нет такого ингредиента!'})
        # else:
        #     raise serializers.ValidationError(
        #         {'ingredients': 'Не все поля заполнены!'})
        return recipe

    def update(self, instance, validated_data):
        print(instance)
        # for field in validated_data:
        #     setattr(instance, field, validated_data[field])
        instance.name = validated_data.get("name", instance.name)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time)
        instance.text = validated_data.get("text", instance.text)
        instance.image = validated_data.get("image", instance.image)
        instance.save()
        validation_field_tags(
            recipe=instance,
            data=self.initial_data,
            field='tags',
            model=Tag,
            through_model=RecipeTag,
            method='PATCH')
        validation_field_ingredients(
            recipe=instance,
            data=self.initial_data,
            field='ingredients',
            model=Ingredient,
            through_model=IngredientIndividual,
            method='PATCH')
        # if 'ingredients' in self.initial_data:
        #     ingredients = self.initial_data.get('ingredients')
        #     for ingredient in ingredients:
        #         amount = ingredient.pop('amount')
        #         current_ingredient = Ingredient.objects.get(**ingredient)
        #         IngredientIndividual.objects.get_or_create(
        #             ingredient=current_ingredient, recipe=instance, amount=amount)
        return instance


class RecipeSerializer(RecipeGetSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CurrentFollowDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return User.objects.get(pk=serializer_field.context['pk'])


class FollowCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    following = serializers.HiddenField(default=CurrentFollowDefault())
    email = serializers.CharField(read_only=True, source='following.email')
    username = serializers.CharField(
        read_only=True, source='following.username')
    first_name = serializers.CharField(
        read_only=True, source='following.first_name')
    last_name = serializers.CharField(
        read_only=True, source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    # recipes = RecipeSerializer(
    #     many=True, read_only=True, source='following.recipes')
    recipes = serializers.SerializerMethodField('paginated_recipes')
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count',
            'user', 'following'
        )
        # extra_kwargs = {'user': {'write_only': True},
        #                 'following': {'write_only': True}}
        model = Follow
        # validators = [
        #     UniqueTogetherValidator(
        #         queryset=model.objects.all(),
        #         fields=('user', 'following'),
        #         message=('Вы уже подписаны на данного пользователя')
        #     )
        # ]

    def paginated_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.following).order_by('id')
        page_size = self.context['request'].query_params.get('recipes_limit') or 10
        paginator = Paginator(recipes, page_size)
        recipe_following = paginator.page(1)
        serializer = RecipeSerializer(recipe_following, many=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        # current_user = User.objects.get(username=self.context.get('request').user)
        # return Follow.objects.get().exists()
        return True

    def get_recipes_count(self, obj):
        # Получить количество рецептов пользователя
        return Recipe.objects.filter(author=obj.following).count()

    def validate(self, data):
        if self.context['request'].user == data['following']:
            raise serializers.ValidationError(
                'Не может быть подписан сам на себя!')
        if Follow.objects.filter(user=data['user'], following=data['following']).exists():
            raise serializers.ValidationError(
                'Уже подписан!')
        return data


# class FollowSerializer(serializers.ModelSerializer):

    # user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # following = serializers.HiddenField(default=CurrentFollowDefault())
    # email = serializers.CharField(read_only=True, source='following.email')
    # username = serializers.CharField(
    #     read_only=True, source='following.username')
    # first_name = serializers.CharField(
    #     read_only=True, source='following.first_name')
    # last_name = serializers.CharField(
    #     read_only=True, source='following.last_name')
    # is_subscribed = serializers.SerializerMethodField()
    # recipes = RecipeSerializer(
    #     many=True, read_only=True, source='following.recipes')
    # recipes_count = serializers.SerializerMethodField()

    # def get_is_subscribed(self, obj):
    #     # current_user = User.objects.get(username=self.context.get('request').user)
    #     # return Follow.objects.get().exists()
    #     return True

    # def get_recipes_count(self, obj):
    #     # Получить количество рецептов пользователя
    #     return Recipe.objects.filter(author=self.context.get('following')).count()

    # class Meta:
    #     fields = (
    #         'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count',
    #         'user', 'following'
    #     )
    #     model = Follow


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
        # fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=('user', 'recipe'),
                message=('Рецепт уже добавлен')
            )
        ]
