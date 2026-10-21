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
    def get_window_minutes(cls):
        from django.conf import settings
        return getattr(settings, 'FAILED_LOGIN_LOCKOUT_MINUTES', 15)

    @classmethod
    def get_max_attempts(cls):
        from django.conf import settings
        return getattr(settings, 'FAILED_LOGIN_LIMIT', 5)

    @classmethod
    def get_failed_attempts_count(cls, email):
        """Returns the number of failed attempts within the sliding window."""
        if not email:
            return 0
        window_start = timezone.now() - timedelta(minutes=cls.get_window_minutes())
        return cls.objects.filter(email__iexact=email.strip(), attempt_time__gte=window_start).count()

    @classmethod
    def is_locked(cls, email):
        """Check if failed attempts meet or exceed the maximum allowed in the last 15 minutes."""
        return cls.get_failed_attempts_count(email) >= cls.get_max_attempts()

    @classmethod
    def get_remaining_attempts(cls, email):
        """Returns remaining attempts allowed before 15-minute lockout."""
        count = cls.get_failed_attempts_count(email)
        return max(0, cls.get_max_attempts() - count)

    @classmethod
    def get_lockout_remaining_seconds(cls, email):
        """
        Returns seconds remaining until lockout expires, or 0 if not locked.
        In a sliding-window limiter, unlocking occurs when the 5th most recent
        attempt ages past the 15-minute window.
        """
        if not email:
            return 0
        max_attempts = cls.get_max_attempts()
        window_minutes = cls.get_window_minutes()
        window_start = timezone.now() - timedelta(minutes=window_minutes)

        recent_attempts = list(
            cls.objects.filter(email__iexact=email.strip(), attempt_time__gte=window_start)
            .order_by('-attempt_time')
            .values_list('attempt_time', flat=True)[:max_attempts]
        )
        if len(recent_attempts) < max_attempts:
            return 0

        oldest_blocking_attempt = recent_attempts[max_attempts - 1]
        unlock_time = oldest_blocking_attempt + timedelta(minutes=window_minutes)
        remaining = (unlock_time - timezone.now()).total_seconds()
        return max(0, int(remaining))

    @classmethod
    def record_failure(cls, email, ip_address=None):
        if email:
            return cls.objects.create(email=email.lower().strip(), ip_address=ip_address)
        return None

    @classmethod
    def clear_failures(cls, email):
        if email:
            cls.objects.filter(email__iexact=email.strip()).delete()

