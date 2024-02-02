from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.models import Follow

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


class CustomUserCreateSerializer(UserSerializer):

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        instance = super().create(validated_data)
        instance.set_password(password)
        instance.save()
        return instance
