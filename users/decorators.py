from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden

def faculty_or_admin_required(view_func):
    """
    Decorator that restricts access to faculty and admin users only.
    Students will be redirected with an error message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('users:login')
        
        if not request.user.has_event_permission():
            messages.error(request, 'Access denied. Only faculty, admin, or students with special permission can create events.')
            return HttpResponseForbidden("Access denied. You need permission to create events.")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def faculty_only_required(view_func):
    """
    Decorator that restricts access to faculty users only.
    Students and admin will be redirected with an error message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('users:login')
        
        if not request.user.is_faculty():
            messages.error(request, 'Access denied. Only faculty members can access this feature.')
            return HttpResponseForbidden("Access denied. Only faculty members can access this feature.")
        
        return view_func(request, *args, **kwargs)
    return wrapper
