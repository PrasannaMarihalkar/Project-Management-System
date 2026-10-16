from .models import Notification

def send_notification(recipient, title, message, link=''):
    """
    Creates an in-app notification for the target user.
    SRS FR-17: Exactly one notification per event.
    """
    if recipient:
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            link=link
        )
    return None
