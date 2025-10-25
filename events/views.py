from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Event
from django import forms
from users.decorators import faculty_or_admin_required

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_date', 'end_date', 'image']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

@login_required
def event_list(request):
    events = Event.objects.all().order_by('-start_date')
    return render(request, 'events/list.html', {'events': events})

@login_required
@faculty_or_admin_required
def create_event(request):
    # Additional server-side validation
    if not request.user.has_event_permission():
        messages.error(request, 'You do not have permission to create events.')
        return redirect('events:list')
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('events:list')
    else:
        form = EventForm()
    return render(request, 'events/form.html', {'form': form, 'title': 'Create Event'})

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'events/detail.html', {'event': event})

@login_required
def attend_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user in event.attendees.all():
        event.attendees.remove(request.user)
        messages.success(request, 'You are no longer attending this event.')
    else:
        event.attendees.add(request.user)
        messages.success(request, 'You are now attending this event!')
    return redirect('events:detail', event_id=event.id)

@login_required
def edit_event(request, event_id):
    """Edit an event - only organizer or admin can edit"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user can edit (organizer or admin)
    if not (request.user == event.organizer or request.user.is_admin_user()):
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('events:detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('events:detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/form.html', {'form': form, 'title': 'Edit Event', 'event': event})

@login_required
def delete_event(request, event_id):
    """Delete an event - only organizer or admin can delete"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user can delete (organizer or admin)
    if not (request.user == event.organizer or request.user.is_admin_user()):
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('events:detail', event_id=event.id)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" has been deleted successfully.')
        return redirect('events:list')
    
    return render(request, 'events/confirm_delete.html', {'event': event})

@login_required
@require_http_methods(["DELETE"])
def ajax_delete_event(request, event_id):
    """AJAX endpoint for deleting an event - only organizer or admin can delete"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user can delete (organizer or admin)
    if not (request.user == event.organizer or request.user.is_admin_user()):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        event_title = event.title
        event.delete()
        return JsonResponse({
            'message': f'Event "{event_title}" has been deleted successfully.'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
