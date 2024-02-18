def get_field(self, obj, model, field):
    object_dict = {
        field: obj.id,
        'user': self.context.get('request').user.id
    }
    return bool(
        self.context.get(
            'request'
        ) and self.context[
            'request'
        ].user.is_authenticated and model.objects.filter(
            **object_dict)
    )


def bulk_create_objects(ingredients, recipe, model):
    objects_of_model = []
    for i in ingredients:
        object_dict = {
            'recipe': recipe,
            'ingredient': i['id'],
            'amount': i['amount']
        }
        objects_of_model.append(model(**object_dict))
    model.objects.bulk_create(objects_of_model)
