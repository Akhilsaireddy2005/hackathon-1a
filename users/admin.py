from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

# Import the models we will register
from .models import User, Notification, PermissionRequest


class CustomUserAdmin(UserAdmin):
    """Admin for the custom User model that uses a 'role' field.

    Uses the existing 'role' CharField (student/faculty/admin) instead of
    a separate boolean flag. When a faculty user is created via admin we
    give them staff privileges and sensible defaults.
    """
    list_display = ('username', 'email', 'department', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'department')
    search_fields = ('username', 'email', 'department')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email', 'department', 'profile_picture')}),
        (_('Role and Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser',
                       'can_create_events', 'can_create_clubs',
                       'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'department', 'role', 'password1', 'password2'),
        }),
    )

    def save_model(self, request, obj, form, change):
        # When creating a new faculty user via admin, promote to staff and
        # enable default permissions for events/clubs.
        if not change and getattr(obj, 'role', None) == 'faculty':
            obj.is_staff = True
            obj.can_create_events = True
            obj.can_create_clubs = True
        super().save_model(request, obj, form, change)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')


class PermissionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission_type', 'status', 'created_at', 'reviewed_by')
    list_filter = ('permission_type', 'status', 'created_at')
    search_fields = ('user__username', 'reason')
    readonly_fields = ('created_at',)


# Register admin classes
admin.site.register(User, CustomUserAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(PermissionRequest, PermissionRequestAdmin)
