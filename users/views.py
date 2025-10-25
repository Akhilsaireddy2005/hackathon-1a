from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView, LogoutView
from django import forms
from django.http import JsonResponse
from django.utils import timezone
import logging
from .models import Notification, PermissionRequest

User = get_user_model()
logger = logging.getLogger(__name__)

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    department = forms.CharField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'department', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'  # Default role is student
        if commit:
            user.save()
        return user

class AdminUserCreateForm(UserCreationForm):
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
    
    # If the notification has a link, redirect there so "View" marks it read and opens the target.
    if notification.link:
        return redirect(notification.link)

    # Fallback: redirect back to notifications page to show updated count
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
        # include optional event fields so students can submit event data
        fields = [
            'permission_type', 'reason',
            'event_title', 'event_description', 'event_location', 'event_start_date', 'event_end_date', 'event_image'
        ]
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Explain why you need this permission...'}),
            'event_description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Event description (if requesting event creation)'}),
            'event_start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'event_end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'event_image': forms.ClearableFileInput(attrs={}),
        }

@login_required
def request_permission(request):
    """Allow students to request permission to create events/clubs"""
    if not request.user.is_student():
        messages.error(request, 'Only students can request permissions.')
        return redirect('home')
    
    if request.method == 'POST':
        logger.info('Received permission request POST from user %s', request.user.username)
        logger.info('Files in request: %s', list(request.FILES.keys()) if request.FILES else 'No files')
        form = PermissionRequestForm(request.POST, request.FILES)
        if not form.is_bound:
            logger.warning('PermissionRequestForm not bound for user %s', request.user.username)
        if form.is_valid():
            try:
                permission_request = form.save(commit=False)
                permission_request.user = request.user
                
                # Handle file upload
                if 'event_image' in request.FILES:
                    file_obj = request.FILES['event_image']
                    logger.info('Processing event_image upload: name=%s size=%s type=%s', 
                              file_obj.name, file_obj.size, file_obj.content_type)
                    
                    # Validate file type
                    if not file_obj.content_type.startswith('image/'):
                        messages.error(request, 'Invalid file type. Please upload an image file.')
                        return render(request, 'users/request_permission.html', {'form': form})
                    
                    permission_request.event_image = file_obj
                    logger.info('Event image attached to permission request')

                # Save permission request
                permission_request.save()
                form.save_m2m()  # Save many-to-many relationships if any
                
                # Verify the image was saved
                if permission_request.event_image:
                    messages.success(request, f'Permission request submitted with image: {permission_request.event_image.name}')
                    logger.info('Permission request %s saved with image at: %s', 
                              permission_request.id, permission_request.event_image.path)
                else:
                    messages.info(request, 'Permission request submitted without an image.')
                
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
                
            except Exception as e:
                logger.error('Error saving permission request: %s', str(e), exc_info=True)
                messages.error(request, 'An error occurred while saving your request. Please try again.')
                return render(request, 'users/request_permission.html', {'form': form})
        else:
            # Log form errors for debugging
            logger.warning('Form validation failed for user %s: %s', request.user.username, form.errors.as_json())
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
def permission_request_detail(request, request_id):
    """Detail view for a single permission request. Faculty/admin can approve or reject from here."""
    permission_request = get_object_or_404(PermissionRequest, id=request_id)

    # Only allow students to view their own request or faculty/admin to review
    if request.user.is_student() and permission_request.user != request.user:
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('users:permission_requests')

    return render(request, 'users/permission_request_detail.html', {'request_obj': permission_request})

@login_required
def approve_permission(request, request_id):
    """Allow faculty/admin to approve permission requests"""
    # Only faculty may approve permission requests
    if not request.user.is_faculty():
        messages.error(request, 'Only faculty can approve permissions.')
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

    # If this was an event creation request, create the Event from stored fields
    if permission_request.permission_type == 'event_creation':
        # grant the user the event creation flag as a backup
        permission_request.user.can_create_events = True
        permission_request.user.save()

        # Only create the Event if the student supplied required data
        if permission_request.event_title and permission_request.event_start_date:
            from events.models import Event
            event = Event(
                title=permission_request.event_title,
                description=permission_request.event_description or permission_request.reason,
                location=permission_request.event_location or 'TBD',
                start_date=permission_request.event_start_date,
                end_date=permission_request.event_end_date or permission_request.event_start_date,
                organizer=permission_request.user,
            )
            # attach image if provided on the request
            if getattr(permission_request, 'event_image', None):
                event.image = permission_request.event_image
            event.save()

            # Notify requester that their event is live and link to its detail page
            create_notification(
                user=permission_request.user,
                title='Event Approved and Published',
                message=f'Your event "{event.title}" was approved and published by {request.user.username}.',
                link=f'/events/{event.id}/'
            )
        else:
            # If required info missing, inform the student they were approved but event not auto-created
            create_notification(
                user=permission_request.user,
                title='Permission Approved',
                message=(f'Your request for {permission_request.get_permission_type_display()} was approved by {request.user.username}, '
                         'but the event was not auto-created because required event details were missing. Please create the event manually.'),
                link='/events/'
            )

    elif permission_request.permission_type == 'club_creation':
        # grant the user club creation permission
        permission_request.user.can_create_clubs = True
        permission_request.user.save()

        # Try to auto-create a Club from the request. Use reasonable defaults if students didn't provide explicit club fields.
        try:
            from clubs.models import Club
            # Derive a club name: if the student provided a short name in the reason (first line), use that; otherwise fallback
            raw = (permission_request.reason or '').strip()
            first_line = raw.splitlines()[0] if raw else ''
            name = first_line[:100] if first_line else f"Club by {permission_request.user.username}"

            club = Club(
                name=name,
                description=permission_request.reason or 'No description provided.',
                president=permission_request.user,
            )
            # If student uploaded an image (event_image used as generic upload), attach it as logo
            if getattr(permission_request, 'event_image', None):
                club.logo = permission_request.event_image
            club.save()
            # add the creator as a member
            club.members.add(permission_request.user)

            create_notification(
                user=permission_request.user,
                title='Club Approved and Created',
                message=f'Your club "{club.name}" was approved and created by {request.user.username}.',
                link=f'/clubs/{club.id}/'
            )
        except Exception:
            # If club creation failed for any reason, at least notify the user of approval
            create_notification(
                user=permission_request.user,
                title='Permission Request Approved',
                message=f'Your request for {permission_request.get_permission_type_display()} has been approved by {request.user.username}.',
                link='/clubs/'
            )

    messages.success(request, f'Permission request approved for {permission_request.user.username}.')
    return redirect('users:permission_requests')

@login_required
def reject_permission(request, request_id):
    """Allow faculty/admin to reject permission requests"""
    # Only faculty may reject permission requests
    if not request.user.is_faculty():
        messages.error(request, 'Only faculty can reject permissions.')
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

@login_required
def create_user(request):
    """Allow admin users to create new users with any role"""
    if not request.user.is_admin_user():
        messages.error(request, 'Only admin users can create new users.')
        return redirect('home')
    
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username} with role {user.get_role_display()}!')
            return redirect('users:user_list')
    else:
        form = AdminUserCreateForm()
    
    return render(request, 'users/create_user.html', {'form': form, 'title': 'Create New User'})
