function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function deleteEvent(eventId) {
    if (!confirm('Are you sure you want to delete this event?')) {
        return;
    }

    const csrftoken = getCookie('csrftoken');
    
    fetch(`/events/api/${eventId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        // Remove the event element from the page
        const eventElement = document.getElementById(`event-${eventId}`);
        if (eventElement) {
            eventElement.remove();
        }
        // If we're on the detail page, redirect to the list page
        if (window.location.pathname.includes('/events/' + eventId)) {
            window.location.href = '/events/';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while deleting the event.');
    });
}