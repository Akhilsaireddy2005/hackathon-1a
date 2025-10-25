from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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

def event_list(request):
    events = Event.objects.all().order_by('-start_date')
    return render(request, 'events/list.html', {'events': events})

@login_required
@faculty_or_admin_required
def create_event(request):
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
