import base64
import imghdr
import uuid

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from rest_framework import serializers
from djoser.serializers import UserSerializer

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Класс поля для закодированной картинки"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                # Разделяем на заголовок и данные
                format, imgstr = data.split(';base64,')
                # Получаем расширение: png, jpeg и т.д.
                ext = format.split('/')[-1]

                # Декодируем Base64
                decoded_file = base64.b64decode(imgstr)

                # Проверяем, что это действительно изображение
                if not self.is_valid_image(decoded_file, ext):
                    raise ValidationError(
                        "Загруженный файл не является"
                        "допустимым изображением."
                    )

                # Генерируем уникальное имя файла
                file_name = f'{uuid.uuid4()}.{ext}'

                # Создаем ContentFile
                data = ContentFile(decoded_file, name=file_name)

            except (TypeError, ValueError, ValidationError):
                self.fail('invalid_image')

        return super().to_internal_value(data)

    def is_valid_image(self, file_data, ext):
        """Проверяет, что файл — действительно изображение
        и совпадает с указанным расширением."""

        # Проверяем, что это реальное изображение
        image_type = imghdr.what(None, h=file_data)
        if image_type not in ('jpg', 'jpeg', 'png', 'webp'):
            return False

        # Проверяем, что расширение соответствует типу изображения
        if ext.lower() not in ('jpg', 'jpeg', 'png', 'webp'):
            return False
        if ext.lower() in ('jpg', 'jpeg') and image_type != 'jpeg':
            return False

        return True


class CustomUserSerializer(UserSerializer):
    """Сериализатор модели пользователя"""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, user):
        request = self.context['request']
        return (
            request
            and request.user.is_authenticated
            and user.authors.filter(subscriber=request.user).exists()
        )
