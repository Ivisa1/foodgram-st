from django.core.validators import RegexValidator

# валидатор имени пользователя
username_validator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message=(
        "Имя пользователя может содержать "
        "только буквы, цифры и @/./+/-/_"),
    code='invalid_username'
)
