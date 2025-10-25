from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LostItem
from django import forms

class LostItemForm(forms.ModelForm):
    class Meta:
        model = LostItem
        fields = ['title', 'description', 'location', 'date', 'image', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

@login_required
def item_list(request):
    items = LostItem.objects.all().order_by('-created_at')
    return render(request, 'lost_found/list.html', {'items': items})

@login_required
def create_item(request):
    if request.method == 'POST':
        form = LostItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, 'Item reported successfully!')
            return redirect('lost_found:list')
    else:
        form = LostItemForm()
    return render(request, 'lost_found/form.html', {'form': form, 'title': 'Report Item'})

@login_required
def item_detail(request, item_id):
    item = get_object_or_404(LostItem, id=item_id)
    return render(request, 'lost_found/detail.html', {'item': item})

@login_required
def update_item(request, item_id):
    item = get_object_or_404(LostItem, id=item_id)
    if request.user != item.user and not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to edit this item.')
        return redirect('lost_found:detail', item_id=item.id)
    
    if request.method == 'POST':
        form = LostItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated successfully!')
            return redirect('lost_found:detail', item_id=item.id)
    else:
        form = LostItemForm(instance=item)
    
    return render(request, 'lost_found/form.html', {'form': form, 'title': 'Update Item'})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(LostItem, id=item_id)
    if request.user != item.user and not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to delete this item.')
        return redirect('lost_found:detail', item_id=item.id)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect('lost_found:list')
    
    return render(request, 'lost_found/confirm_delete.html', {'item': item})
