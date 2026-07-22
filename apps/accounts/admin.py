from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
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
        ('Personal Information', {
            'fields': (
                'full_name', 'office_id', 'designation', 'email',
                'phone', 'blood_group', 'date_of_birth', 'facebook_id',
            ),
        }),
        ('The Right', {
            'fields': (
                'is_admin', 'is_founder', 'is_active',
                'is_staff', 'is_superuser', 'groups', 'user_permissions',
            ),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_at', 'is_active')
    list_filter = ('is_active', 'login_at')
    search_fields = ('user__username', 'ip_address')
    ordering = ('-login_at',)
