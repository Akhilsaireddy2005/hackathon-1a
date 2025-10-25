from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Club
from django import forms
from users.decorators import faculty_or_admin_required

class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'description', 'logo']

def club_list(request):
    clubs = Club.objects.all().order_by('name')
    return render(request, 'clubs/list.html', {'clubs': clubs})

@login_required
@faculty_or_admin_required
def create_club(request):
    if request.method == 'POST':
        form = ClubForm(request.POST, request.FILES)
        if form.is_valid():
            club = form.save(commit=False)
            club.president = request.user
            club.save()
            club.members.add(request.user)  # Add creator as a member
            messages.success(request, 'Club created successfully!')
            return redirect('clubs:list')
    else:
        form = ClubForm()
    return render(request, 'clubs/form.html', {'form': form, 'title': 'Create Club'})

def club_detail(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    return render(request, 'clubs/detail.html', {'club': club})

@login_required
def join_club(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    if request.user in club.members.all():
        club.members.remove(request.user)
        messages.success(request, 'You have left the club.')
    else:
        club.members.add(request.user)
        messages.success(request, 'You have joined the club!')
    return redirect('clubs:detail', club_id=club.id)
