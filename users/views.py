from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView, LogoutView
from django import forms
from django.http import JsonResponse
from .models import Notification

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    department = forms.CharField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'department', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    department = forms.CharField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'department', 'profile_picture']

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            # Create welcome notification
            Notification.objects.create(
                user=user,
                title="Welcome to Smart Campus!",
                message=f"Welcome {username}! Your account has been created successfully.",
                link="/users/profile/"
            )
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('users:login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('users:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    # Get user's activities
    from events.models import Event
    from lost_found.models import LostItem
    from clubs.models import Club
    from feedback.models import Feedback
    
    user_events = Event.objects.filter(attendees=request.user).order_by('-start_date')[:5]
    user_lost_items = LostItem.objects.filter(user=request.user).order_by('-created_at')[:5]
    user_clubs = Club.objects.filter(members=request.user).order_by('-created_at')[:5]
    user_feedback = Feedback.objects.filter(user=request.user).order_by('-created_at')[:5]
    unread_notifications = request.user.notifications.filter(is_read=False)
    
    context = {
        'form': form,
        'user_events': user_events,
        'user_lost_items': user_lost_items,
        'user_clubs': user_clubs,
        'user_feedback': user_feedback,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def notifications(request):
    notifications = request.user.notifications.all()
    unread_count = request.user.notifications.filter(is_read=False).count()
    return render(request, 'users/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # Always redirect back to notifications page to show updated count
    return redirect('users:notifications')

def create_notification(user, title, message, link=None):
    """Utility function to create notifications from anywhere in the app"""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link
    )

class CustomLoginView(LoginView):
    """Custom login view that redirects to the correct profile URL"""
    template_name = 'users/login.html'
    
    def get_success_url(self):
        return '/users/profile/'

class CustomLogoutView(LogoutView):
    """Custom logout view that redirects to home page"""
    template_name = 'users/logout.html'
    
    def get_success_url(self):
        return '/'

@login_required
def logout_view(request):
    """Simple logout function view"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')
