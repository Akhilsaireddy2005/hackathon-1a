from django import template

register = template.Library()

@register.filter
def can_create_events(user):
    """Check if user can create events (faculty or admin only)"""
    if not user.is_authenticated:
        return False
    return not user.is_student()

@register.filter
def can_create_clubs(user):
    """Check if user can create clubs (faculty or admin only)"""
    if not user.is_authenticated:
        return False
    return not user.is_student()

@register.filter
def is_faculty_or_admin(user):
    """Check if user is faculty or admin"""
    if not user.is_authenticated:
        return False
    return user.is_faculty() or user.is_admin_user()
