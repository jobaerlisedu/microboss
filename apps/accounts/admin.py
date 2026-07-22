from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'full_name', 'office_id', 'designation',
        'email', 'phone', 'is_admin', 'is_founder', 'is_active',
    )
    list_filter = ('is_admin', 'is_founder', 'is_active', 'blood_group')
    search_fields = ('username', 'full_name', 'email', 'office_id', 'phone')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('ব্যক্তিগত তথ্য'), {
            'fields': (
                'full_name', 'office_id', 'designation', 'email',
                'phone', 'blood_group', 'date_of_birth', 'facebook_id',
            ),
        }),
        (_('অধিকার'), {
            'fields': (
                'is_admin', 'is_founder', 'is_active',
                'is_staff', 'is_superuser', 'groups', 'user_permissions',
            ),
        }),
        (_('গুরুত্বপূর্ণ তারিখ'), {
            'fields': ('last_login', 'date_joined'),
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_at', 'is_active')
    list_filter = ('is_active', 'login_at')
    search_fields = ('user__username', 'ip_address')
    ordering = ('-login_at',)
