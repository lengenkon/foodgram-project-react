import base64
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from recipes.models import (
    Tag, Ingredient, Recipe, Follow,
    IngredientIndividual, RecipeTag, Favorites, ShoppingList)
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


class IngredientIndividualSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='ingredient.name')
    measurement_unit = serializers.CharField(
        read_only=True, source='ingredient.measurement_unit')
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = IngredientIndividual
        fields = ('id', 'amount', 'name', 'measurement_unit')

    # Валидация в модели
    # def validate(self, data):
    #     if data['amount'] < 1:
    #         raise serializers.ValidationError({'amount': ['Количество должно быть больше 1']})
    #     return data


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
        amount = [int(element['amount']) for element in ingredients]
        ingredient = [
            Ingredient.objects.get(
                id=int(element['ingredient']['id'])) for element in ingredients
        ]
        RecipeTag.objects.bulk_create(
            [RecipeTag(recipe=recipe,
                       tag=Tag.objects.get(id=id)) for id in tags])
        objects_of_model = []
        for i in range(len(ingredients)):
            object_dict = {
                'recipe':  recipe,
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


class RecipeCreateSerializer(RecipeGetSerializer):

    class Meta:
        fields = (
            'id', 'tags', 'author',
            'name', 'image', 'cooking_time', 'text',
            'ingredients',
            'is_favorited', 'is_in_shopping_cart'
        )
        model = Recipe

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

    # def validate_tags(self, tags):
    #     if not tags:
    #         raise serializers.ValidationError(['Не должно быть пустым!'])
    #     instance_list = []
    #     for element in tags:
    #         try:
    #             instance = Tag.objects.get(id=element)
    #         except Ingredient.DoesNotExist:
    #             raise serializers.ValidationError(
    #                 {'tags': 'Нет такого тэга!'})
    #         if instance in instance_list:
    #             raise serializers.ValidationError(['Уже добавлен в этот рецепт!'])
    #         instance_list.append(instance)
    #     return tags

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredientindividual_set')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        # tags = validate_field(model=Tag,
        #                       data=self.initial_data.get('tags'),
        #                       field='tags')
        # ingredients = validate_field(model=Ingredient,
        #                              data=self.initial_data.get('ingredients'),
        #                              field='ingredient')
        amount = [int(element['amount']) for element in ingredients]
        ingredient = [
            Ingredient.objects.get(
                id=int(element['ingredient']['id'])) for element in ingredients
        ]
        RecipeTag.objects.bulk_create([RecipeTag(recipe=recipe, tag=Tag.objects.get(id=id)) for id in tags])
        objects_of_model = []
        for i in range(len(ingredients)):
            object_dict = {
                'recipe':  recipe,
                'ingredient': ingredient[i],
                'amount': amount[i]
            }
            objects_of_model.append(IngredientIndividual(**object_dict))
        IngredientIndividual.objects.bulk_create(objects_of_model)
        # recipe.save()
        print(recipe.ingredients.all())
        print(recipe.tags.all())
        return recipe



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
        # validation_field_ingredients(
        #     recipe=recipe,
        #     data=self.initial_data,
        #     field='ingredients',
        #     model=Ingredient,
        #     through_model=IngredientIndividual)
        # validation_field_tags(
        #     recipe=recipe,
        #     data=self.initial_data,
        #     field='tags',
        #     model=Tag,
        #     through_model=RecipeTag)
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
        # return recipe

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

        # print(instance)
        # print(validated_data)
        # # for field in validated_data:
        # #     setattr(instance, field, validated_data[field])
        # instance.name = validated_data.get("name", instance.name)
        # instance.cooking_time = validated_data.get(
        #     "cooking_time", instance.cooking_time)
        # instance.text = validated_data.get("text", instance.text)
        # instance.image = validated_data.get("image", instance.image)
        # instance.save()
        # recipe = instance
        # tags = validate_field(model=Tag,
        #                       data=self.initial_data.get('tags'),
        #                       field='tags',
        #                       model_through=RecipeTag)
        # ingredients = validate_field(model=Ingredient,
        #                              data=self.initial_data.get('ingredients'),
        #                              field='ingredient',
        #                              model_through=IngredientIndividual)
        # amount = [element['amount'] for element in self.initial_data.get(
        #         'ingredients')]
        # RecipeTag.objects.bulk_create([RecipeTag(recipe=recipe, tag=tag) for tag in tags])
        # objects_of_model = []
        # for i in range(len(ingredients)):
        #     object_dict = {
        #         'recipe':  recipe,
        #         'ingredient': ingredients[i],
        #         'amount': amount[i]
        #     }
        #     objects_of_model.append(IngredientIndividual(**object_dict))
        # IngredientIndividual.objects.bulk_create(objects_of_model)

        # validation_field_tags(
        #     recipe=instance,
        #     data=self.initial_data,
        #     field='tags',
        #     model=Tag,
        #     through_model=RecipeTag,
        #     method='PATCH')
        # validation_field_ingredients(
        #     recipe=instance,
        #     data=self.initial_data,
        #     field='ingredients',
        #     model=Ingredient,
        #     through_model=IngredientIndividual,
        #     method='PATCH')
        # # if 'ingredients' in self.initial_data:
        # #     ingredients = self.initial_data.get('ingredients')
        # #     for ingredient in ingredients:
        # #         amount = ingredient.pop('amount')
        # #         current_ingredient = Ingredient.objects.get(**ingredient)
        # #         IngredientIndividual.objects.get_or_create(
        # #             ingredient=current_ingredient, recipe=instance, amount=amount)
        # return instance


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
        recipes = Recipe.objects.filter(author=obj.following).order_by('id')
        page_size = self.context['request'].query_params.get('recipes_limit') or 10
        paginator = Paginator(recipes, page_size)
        recipe_following = paginator.page(1)
        serializer = RecipeSerializer(recipe_following, many=True)
        return serializer.data

    def get_is_subscribed(self, obj):
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
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=('user', 'recipe'),
                message=('Рецепт уже добавлен')
            )
        ]
