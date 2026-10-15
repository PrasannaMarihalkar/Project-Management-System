from django.db import models
from django.conf import settings
from django.utils import timezone

class Project(models.Model):
    """
    SRS FR-03 & FR-16: Project entity with lifecycle states (Active / Archived).
    Creator becomes Owner upon creation.
    Archived projects are read-only.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(default=timezone.now)
    target_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    archived_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_archived(self):
        return self.archived_at is not None

    def __str__(self):
        return f"{self.name} ({'Archived' if self.is_archived else 'Active'})"


class Membership(models.Model):
    """
    SRS FR-04 & SR-01: Project membership and role-based access control.
    Enforces unique membership per user/project.
    """
    ROLE_OWNER = 'Owner'
    ROLE_MANAGER = 'Manager'
    ROLE_MEMBER = 'Member'

    ROLE_CHOICES = [
        (ROLE_OWNER, 'Owner'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_MEMBER, 'Member'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')
        ordering = ['role', 'user__email']

    def __str__(self):
        return f"{self.user.email} - {self.role} in {self.project.name}"
