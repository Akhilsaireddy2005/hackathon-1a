from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView, LogoutView
from django import forms
from django.http import JsonResponse
from .models import Notification, PermissionRequest

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

# Permission Request Views
class PermissionRequestForm(forms.ModelForm):
    class Meta:
        model = PermissionRequest
        fields = ['permission_type', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Explain why you need this permission...'}),
        }

@login_required
def request_permission(request):
    """Allow students to request permission to create events/clubs"""
    if not request.user.is_student():
        messages.error(request, 'Only students can request permissions.')
        return redirect('home')
    
    if request.method == 'POST':
        form = PermissionRequestForm(request.POST)
        if form.is_valid():
            permission_request = form.save(commit=False)
            permission_request.user = request.user
            permission_request.save()
            
            # Notify faculty and admin about the request
            faculty_and_admin_users = User.objects.filter(role__in=['faculty', 'admin'])
            for user in faculty_and_admin_users:
                create_notification(
                    user=user,
                    title=f'Permission Request from {request.user.username}',
                    message=f'Permission Type: {permission_request.get_permission_type_display()}\nReason: {permission_request.reason[:100]}...',
                    link=f'/users/permission-requests/{permission_request.id}/'
                )
            
            messages.success(request, 'Permission request submitted successfully! Faculty and admin have been notified.')
            return redirect('users:permission_requests')
    else:
        form = PermissionRequestForm()
    
    return render(request, 'users/request_permission.html', {'form': form})

@login_required
def permission_requests(request):
    """Show user's permission requests"""
    if request.user.is_student():
        requests = request.user.permission_requests.all()
    else:
        requests = PermissionRequest.objects.filter(status='pending')
    
    return render(request, 'users/permission_requests.html', {'requests': requests})

@login_required
def approve_permission(request, request_id):
    """Allow faculty/admin to approve permission requests"""
    if not (request.user.is_faculty() or request.user.is_admin_user()):
        messages.error(request, 'Only faculty and admin can approve permissions.')
        return redirect('home')
    
    permission_request = get_object_or_404(PermissionRequest, id=request_id)
    
    if permission_request.status != 'pending':
        messages.error(request, 'This request has already been processed.')
        return redirect('users:permission_requests')
    
    # Approve the request
    permission_request.status = 'approved'
    permission_request.reviewed_by = request.user
    permission_request.reviewed_at = timezone.now()
    permission_request.save()
    
    # Grant permission to user
    if permission_request.permission_type == 'event_creation':
        permission_request.user.can_create_events = True
    elif permission_request.permission_type == 'club_creation':
        permission_request.user.can_create_clubs = True
    permission_request.user.save()
    
    # Notify the user
    create_notification(
        user=permission_request.user,
        title='Permission Request Approved',
        message=f'Your request for {permission_request.get_permission_type_display()} has been approved by {request.user.username}.',
        link='/events/' if permission_request.permission_type == 'event_creation' else '/clubs/'
    )
    
    messages.success(request, f'Permission request approved for {permission_request.user.username}.')
    return redirect('users:permission_requests')

@login_required
def reject_permission(request, request_id):
    """Allow faculty/admin to reject permission requests"""
    if not (request.user.is_faculty() or request.user.is_admin_user()):
        messages.error(request, 'Only faculty and admin can reject permissions.')
        return redirect('home')
    
    permission_request = get_object_or_404(PermissionRequest, id=request_id)
    
    if permission_request.status != 'pending':
        messages.error(request, 'This request has already been processed.')
        return redirect('users:permission_requests')
    
    # Reject the request
    permission_request.status = 'rejected'
    permission_request.reviewed_by = request.user
    permission_request.reviewed_at = timezone.now()
    permission_request.save()
    
    # Notify the user
    create_notification(
        user=permission_request.user,
        title='Permission Request Rejected',
        message=f'Your request for {permission_request.get_permission_type_display()} has been rejected by {request.user.username}.',
        link='/users/permission-requests/'
    )
    
    messages.success(request, f'Permission request rejected for {permission_request.user.username}.')
    return redirect('users:permission_requests')

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
