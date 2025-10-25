from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

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
        
        if request.user.is_student():
            messages.error(request, 'Access denied. Only faculty and admin can create events and clubs.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper
