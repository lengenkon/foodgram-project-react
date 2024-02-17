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
