from datetime import timedelta
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifiers for auth."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model using email for login as specified in SRS FR-01."""
    username = None
    email = models.EmailField('email address', unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.full_name or self.email


class FailedLoginAttempt(models.Model):
    """
    Tracks failed logins to enforce 15-minute lockout after 5 failures
    as mandated by SRS SR-05 and TC-15.
    """
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    attempt_time = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-attempt_time']

    @classmethod
    def is_locked(cls, email):
        """Check if 5 or more failed attempts occurred in the last 15 minutes."""
        window_start = timezone.now() - timedelta(minutes=15)
        count = cls.objects.filter(email__iexact=email, attempt_time__gte=window_start).count()
        return count >= 5

    @classmethod
    def record_failure(cls, email, ip_address=None):
        cls.objects.create(email=email.lower().strip(), ip_address=ip_address)

    @classmethod
    def clear_failures(cls, email):
        cls.objects.filter(email__iexact=email).delete()
