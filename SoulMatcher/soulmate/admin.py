from django.contrib import admin

from .models import CustomUser, Aspect, Attitude, Weight, Priority


class PriorityInline(admin.TabularInline):
    model = Priority.users.through
    raw_id_fields = ('priority',)
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'email_confirmed')
    list_filter = ('email_confirmed',)
    search_fields = ('username', 'email')
    inlines = [PriorityInline]


@admin.register(Aspect)
class AspectAdmin(admin.ModelAdmin):
    list_display = ('aspect',)
    search_fields = ('aspect',)


@admin.register(Attitude)
class AttitudeAdmin(admin.ModelAdmin):
    list_display = ('attitude',)
    search_fields = ('attitude',)


@admin.register(Weight)
class WeightAdmin(admin.ModelAdmin):
    list_display = ('weight',)
    search_fields = ('weight',)


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ('aspect', 'attitude', 'weight')
    list_filter = ('aspect', 'attitude', 'weight')
    search_fields = ('aspect__aspect', 'attitude__attitude', 'weight__weight')
    filter_horizontal = ('users',)
