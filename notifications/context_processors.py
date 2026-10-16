from .models import Notification

def unread_notifications(request):
    """Context processor exposing unread notification count to all templates."""
    if request.user.is_authenticated:
        unread_qs = Notification.objects.filter(recipient=request.user, is_read=False)
        return {
            'unread_notifications_count': unread_qs.count(),
            'latest_notifications': unread_qs[:5],
        }
    return {
        'unread_notifications_count': 0,
        'latest_notifications': [],
    }
