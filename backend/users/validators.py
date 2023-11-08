import re

from django.core.exceptions import ValidationError

FAILED_NAME = 'me'


def username_validator(value):
    if not re.search(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            r'Используйте только буквы, цифры и символы @/./+/-/_'
        )

    if value == FAILED_NAME:
        raise ValidationError(
            f'Использовать имя {FAILED_NAME} в качестве username запрещено'
        )
    return value
