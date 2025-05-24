from django.contrib.auth import get_user_model

from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserUserSerializer

from drf_extra_fields.fields import Base64ImageField

User = get_user_model()


class CustomUserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя"""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, user):
        request = self.context['request']
        return (
            request
            and request.user.is_authenticated
            and user.authors.filter(subscriber=request.user).exists()
        )
