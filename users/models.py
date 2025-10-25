from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    can_create_events = models.BooleanField(default=False)
    can_create_clubs = models.BooleanField(default=False)
    
    def is_student(self):
        return self.role == 'student'
    
    def is_faculty(self):
        return self.role == 'faculty'
    
    def is_admin_user(self):
        return self.role == 'admin'
    
    def has_event_permission(self):
        """Check if user can create events (faculty/admin or has special permission)"""
        return self.is_faculty() or self.is_admin_user() or self.can_create_events
    
    def has_club_permission(self):
        """Check if user can create clubs (faculty/admin or has special permission)"""
        return self.is_faculty() or self.is_admin_user() or self.can_create_clubs


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class PermissionRequest(models.Model):
    PERMISSION_CHOICES = (
        ('event_creation', 'Event Creation'),
        ('club_creation', 'Club Creation'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permission_requests')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_CHOICES)
    reason = models.TextField()
    # Optional event data (used when permission_type == 'event_creation')
    event_title = models.CharField(max_length=200, blank=True, null=True)
    event_description = models.TextField(blank=True, null=True)
    event_location = models.CharField(max_length=200, blank=True, null=True)
    event_start_date = models.DateTimeField(null=True, blank=True)
    event_end_date = models.DateTimeField(null=True, blank=True)
    event_image = models.ImageField(upload_to='event_images', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_permission_type_display()}"
