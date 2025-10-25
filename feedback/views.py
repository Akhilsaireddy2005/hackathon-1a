from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Feedback
from django import forms
from users.models import User
from users.views import create_notification

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['title', 'description', 'category']

@login_required
def feedback_list(request):
    feedback = Feedback.objects.all().order_by('-created_at')
    return render(request, 'feedback/list.html', {'feedback_list': feedback})

@login_required
def create_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            
            # Send notification to all faculty and admin users
            faculty_and_admin_users = User.objects.filter(role__in=['faculty', 'admin'])
            for user in faculty_and_admin_users:
                create_notification(
                    user=user,
                    title=f'New Feedback from {request.user.username}',
                    message=f'Category: {feedback.category}\nTitle: {feedback.title}\nDescription: {feedback.description[:100]}...',
                    link=f'/feedback/{feedback.id}/'
                )
            
            messages.success(request, 'Feedback submitted successfully! Faculty and admin have been notified.')
            return redirect('feedback:list')
    else:
        form = FeedbackForm()
    return render(request, 'feedback/form.html', {'form': form, 'title': 'Submit Feedback'})

@login_required
def feedback_detail(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    return render(request, 'feedback/detail.html', {'feedback': feedback})
