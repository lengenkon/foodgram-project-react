from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.models import Follow

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        # self.context['request'].user == data['following']:
        # # request = self.context.get('request', None)
        # return Follow.objects.filter(
        #     user=obj.user, following=obj.following).exists()
        
        current_user = User.objects.get(username=self.context.get('request').user)
        return Follow.objects.filter(
            following=obj.id, user=current_user.id).exists()
        # following = current_user.following.all().values_list('following', flat=True)
        # return obj.id in following


class CustomUserCreateSerializer(UserSerializer):

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password')
        write_only = ('password, ')
