import json
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import User, FailedLoginAttempt

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

@ensure_csrf_cookie
@require_http_methods(['GET', 'POST'])
def register_view(request):
    """
    SRS FR-01 & TC-01: Account registration.
    Allows new users to register with a unique email address and password.
    Rejects duplicate email addresses without creating a duplicate record.
    """
    if request.user.is_authenticated:
        return redirect('projects:project_list')

    if request.method == 'GET':
        return render(request, 'accounts/register.html')

    is_json = request.content_type == 'application/json' or 'application/json' in request.headers.get('Accept', '')
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': {'code': 'INVALID_JSON', 'message': 'Invalid JSON body'}}, status=400)
        email = payload.get('email', '').strip().lower()
        password = payload.get('password', '')
        full_name = payload.get('full_name', '').strip()
    else:
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        full_name = request.POST.get('full_name', '').strip()

    if not email or not password:
        msg = "Email and password are required."
        if is_json:
            return JsonResponse({'error': {'code': 'BAD_REQUEST', 'message': msg}}, status=400)
        messages.error(request, msg)
        return render(request, 'accounts/register.html', status=400)

    if len(password) < 8:
        msg = "Password must be at least 8 characters long."
        if is_json:
            return JsonResponse({'error': {'code': 'WEAK_PASSWORD', 'message': msg}}, status=400)
        messages.error(request, msg)
        return render(request, 'accounts/register.html', status=400)

    # Check email duplicate (FR-01 / TC-01)
    if User.objects.filter(email__iexact=email).exists():
        msg = "An account with this email address already exists."
        if is_json:
            return JsonResponse({'error': {'code': 'DUPLICATE_EMAIL', 'message': msg}}, status=400)
        messages.error(request, msg)
        return render(request, 'accounts/register.html', status=400)

    # Create account
    user = User.objects.create_user(email=email, password=password, full_name=full_name)
    login(request, user)

    if is_json:
        return JsonResponse({
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'message': 'Account created successfully'
        }, status=201)

    messages.success(request, "Registration successful! Welcome to the Project Management System.")
    return redirect('projects:project_list')


@ensure_csrf_cookie
@require_http_methods(['GET', 'POST'])
def login_view(request):
    """
    SRS FR-02 & SR-05 & TC-02 & TC-15: Authentication and failed-login lockout.
    Enforces 15-minute lockout after 5 consecutive failed logins.
    """
    if request.user.is_authenticated:
        return redirect('projects:project_list')

    if request.method == 'GET':
        return render(request, 'accounts/login.html')

    is_json = request.content_type == 'application/json' or 'application/json' in request.headers.get('Accept', '')
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': {'code': 'INVALID_JSON', 'message': 'Invalid JSON body'}}, status=400)
        email = payload.get('email', '').strip().lower()
        password = payload.get('password', '')
    else:
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

    if not email or not password:
        msg = "Email and password are required."
        if is_json:
            return JsonResponse({'error': {'code': 'BAD_REQUEST', 'message': msg}}, status=400)
        messages.error(request, msg)
        return render(request, 'accounts/login.html', {'email': email}, status=400)

    ip_address = get_client_ip(request)

    # Check SR-05 Lockout
    if FailedLoginAttempt.is_locked(email):
        remaining_seconds = FailedLoginAttempt.get_lockout_remaining_seconds(email)
        remaining_minutes = max(1, (remaining_seconds + 59) // 60)
        msg = f"Too many failed login attempts. Account temporarily locked for {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}."
        if is_json:
            response = JsonResponse({
                'error': {
                    'code': 'LOCKED_OUT',
                    'message': msg,
                    'retry_after_seconds': remaining_seconds
                }
            }, status=429)
            response['Retry-After'] = str(remaining_seconds)
            return response

        messages.error(request, msg)
        response = render(request, 'accounts/login.html', {
            'locked_out': True,
            'retry_after_seconds': remaining_seconds,
            'remaining_minutes': remaining_minutes,
            'email': email,
        }, status=429)
        response['Retry-After'] = str(remaining_seconds)
        return response

    user = authenticate(request, email=email, password=password)
    if user is not None:
        # Success: clear failed attempts and open session
        FailedLoginAttempt.clear_failures(email)
        login(request, user)
        if is_json:
            return JsonResponse({
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'message': 'Login successful'
            }, status=200)
        return redirect('projects:project_list')
    else:
        # Record failure (SR-05)
        FailedLoginAttempt.record_failure(email, ip_address)
        attempts_left = FailedLoginAttempt.get_remaining_attempts(email)

        if attempts_left > 0:
            msg = f"Invalid email or password. {attempts_left} attempt{'s' if attempts_left != 1 else ''} remaining before a 15-minute account lockout."
        else:
            msg = "Invalid email or password. Maximum failed attempts reached. Account is now locked for 15 minutes."

        if is_json:
            return JsonResponse({
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': msg,
                    'attempts_remaining': attempts_left
                }
            }, status=401)

        messages.error(request, msg)
        return render(request, 'accounts/login.html', {
            'email': email,
            'attempts_remaining': attempts_left,
        }, status=401)


@require_http_methods(['GET', 'POST'])
def logout_view(request):
    """SRS FR-02: User logout."""
    logout(request)
    if request.content_type == 'application/json':
        return JsonResponse({'message': 'Logged out successfully'}, status=200)
    return redirect('accounts:login')
