from django.contrib import admin
from .models import CustomUser, Priority


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'email_confirmed']
    list_filter = ['email_confirmed']
    search_fields = ['username', 'email']
    # Дополнительные настройки админки для CustomUser


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ['aspect', 'attitude', 'weight', 'user']
    list_filter = ['aspect', 'attitude']
    search_fields = ['aspect', 'attitude', 'user__username']
    # Дополнительные настройки админки для Priority
