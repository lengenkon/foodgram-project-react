from rest_framework import serializers


def validation_field(recipe, data, field, model, through_model):    
    if data.get(field, False):
        ingredients = data.get(field)
        for ingredient in ingredients:
            # amount = ingredient.pop('amount')
            if isinstance(ingredient, dict):
                id = ingredient['id']
            else:
                id = ingredient
            if model.objects.filter(id=id).exists():
                current_ingredient = model.objects.get(id=id)
                if through_model.objects.filter(ingredient=current_ingredient, recipe=recipe).exists():
                    raise serializers.ValidationError({field: ['Этот ингредиент уже добавлен в этот рецепт!']})
                if 'amount' in ingredient:
                    if ingredient['amount'] >= 1:
                        through_model.objects.create(
                            ingredient=current_ingredient, recipe=recipe, amount=ingredient['amount'])
                    else:
                        raise serializers.ValidationError({'amount': ['Количество должно быть больше 1']})
                else:
                    through_model.objects.create(
                        field_name=current_ingredient, recipe=recipe)
            else:
                raise serializers.ValidationError({field: ['Нет такого ингредиента!']})
    else:
        raise serializers.ValidationError(
            {field: ['Не все поля заполнены!']})
    

def validation_field_ingredients(recipe, data, field, model, through_model, method='POST'):    
    if data.get(field, False):
        ingredients = data.get(field)
        for ingredient in ingredients:
            amount = ingredient.pop('amount')
            if model.objects.filter(id=ingredient['id']).exists():
                current_ingredient = model.objects.get(id=ingredient['id'])
                if through_model.objects.filter(ingredient=current_ingredient, recipe=recipe).exists():
                    if method == 'PATCH':
                        continue
                    raise serializers.ValidationError({field: ['Этот ингредиент уже добавлен в этот рецепт!']})
                if amount >= 1:
                    through_model.objects.create(
                        ingredient=current_ingredient, recipe=recipe, amount=amount)
                else:
                    raise serializers.ValidationError({'amount': ['Количество должно быть больше 1']})
            else:
                raise serializers.ValidationError({field: ['Нет такого ингредиента!']})
    else:
        raise serializers.ValidationError(
            {field: ['Не все поля заполнены!']})


def validation_field_tags(recipe, data, field, model, through_model, method='POST'):
    if data.get(field, False):
        tags = data.get('tags')
        for tag in tags:
            if model.objects.filter(id=tag).exists():
                current_tag = model.objects.get(pk=tag)
                if through_model.objects.filter(tag=current_tag, recipe=recipe).exists():
                    if method == 'PATCH':
                        continue
                    raise serializers.ValidationError(
                        {'tags': ['Этот tag уже добавлен в этот рецепт!']})
                through_model.objects.create(recipe=recipe, tag=current_tag)
            else:
                raise serializers.ValidationError(
                    {'tags': 'Нет такого ингредиента!'})
    else:
        raise serializers.ValidationError(
            {'tags': ['Обязательное поле']})

