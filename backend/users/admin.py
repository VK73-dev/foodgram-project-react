from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Subscription, User

EMPTY_MESSAGE = '-пусто-'


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'count_subscribers', 'count_recipes')
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')
    ordering = ('username', )
    empty_value_display = EMPTY_MESSAGE

    def count_subscribers(self, obj):
        return obj.subscriber.count()

    def count_recipes(self, obj):
        return obj.recipes.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = (
        'author__username',
        'author__email',
        'user__username',
        'user__email'
    )
    list_filter = ('author__username', 'user__username')
    empty_value_display = EMPTY_MESSAGE
