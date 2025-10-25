from django import template

register = template.Library()

@register.filter
def can_create_events(user):
    """Check if user can create events (faculty/admin or has special permission)"""
    if not user.is_authenticated:
        return False
    return user.has_event_permission()

@register.filter
def can_create_clubs(user):
    """Check if user can create clubs (faculty/admin or has special permission)"""
    if not user.is_authenticated:
        return False
    return user.has_club_permission()

@register.filter
def is_faculty_or_admin(user):
    """Check if user is faculty or admin"""
    if not user.is_authenticated:
        return False
    return user.is_faculty() or user.is_admin_user()

@register.filter
def can_request_permission(user):
    """Check if user can request permission (students only)"""
    if not user.is_authenticated:
        return False
    return user.is_student()
