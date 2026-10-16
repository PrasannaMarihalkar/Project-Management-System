from django.db import models
from django.conf import settings
from projects.models import Project

class ActivityEvent(models.Model):
    """
    SRS FR-13 & TC-07: Activity history and audit trail.
    Records project membership changes, task creation, edits, status transitions,
    and archival events with actor, action, entity and timestamp in chronological order.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='audit_events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_actions')
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'created_at']),
        ]

    def __str__(self):
        actor_email = self.actor.email if self.actor else "System"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {actor_email} - {self.action} on {self.entity_type} ({self.entity_id})"
