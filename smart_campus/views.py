from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from events.models import Event
from lost_found.models import LostItem
from clubs.models import Club

def home(request):
    """Home page view for the Smart Campus Ecosystem"""
    if request.user.is_authenticated:
        # Get recent events, lost items, and clubs for authenticated users
        events = Event.objects.all().order_by('-start_date')[:3]
        lost_items = LostItem.objects.filter(status='lost').order_by('-created_at')[:3]
        clubs = Club.objects.all().order_by('?')[:3]  # Random selection
        
        context = {
            'events': events,
            'lost_items': lost_items,
            'clubs': clubs,
        }
    else:
        # Empty context for non-authenticated users
        context = {
            'events': [],
            'lost_items': [],
            'clubs': [],
        }
    
    return render(request, 'base/home.html', context)