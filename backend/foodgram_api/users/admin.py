from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.admin import BaseAdmin

from .models import User, Follow


@admin.register(User)
class CustomUserAdmin(UserAdmin, BaseAdmin):
    """Класс для пользователей"""

    list_display = ('username', 'id', 'email', 'first_name', 'last_name')
    search_fields = ('email', 'username')
    list_filter = ('email', 'username')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'id', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Follow)
class FollowAdmin(BaseAdmin):
    """Класс для подписок"""
    
    list_display = ('id', 'subscriber', 'author')
    search_fields = ('subscriber__username', 'author__username')
    fields = ('id', 'subscriber', 'author')
