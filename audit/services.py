from .models import ActivityEvent

def log_audit_event(project, actor, action, entity_type, entity_id='', details=''):
    """
    Appends an immutable audit log record.
    Must be called inside the active transaction so mutation and audit commit atomically.
    (SRS FR-13, SAD §3.4, §3.5).
    """
    return ActivityEvent.objects.create(
        project=project,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        details=details
    )
