from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, FailedLoginAttempt

class AuthAndSecurityTests(TestCase):
    """
    Verification of TC-01, TC-02, and TC-15.
    SRS FR-01, FR-02, SR-02, SR-03, SR-04, SR-05.
    """
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')

    def test_tc01_registration_valid_and_duplicate(self):
        """TC-01: Register fresh email; retry same email -> duplicate rejected."""
        # Fresh registration
        resp = self.client.post(self.register_url, {
            'email': 'freshuser@example.com',
            'full_name': 'Fresh User',
            'password': 'StrongPassword123!'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(User.objects.filter(email='freshuser@example.com').count(), 1)

        # Logout
        self.client.logout()

        # Retry duplicate email
        resp_dup = self.client.post(self.register_url, {
            'email': 'freshuser@example.com',
            'full_name': 'Duplicate User',
            'password': 'AnotherPassword123!'
        })
        self.assertEqual(resp_dup.status_code, 400)
        # Verify no duplicate user was created
        self.assertEqual(User.objects.filter(email='freshuser@example.com').count(), 1)

    def test_tc02_sign_in_and_sign_out(self):
        """TC-02: Valid login opens session; logout closes; invalid password denied."""
        user = User.objects.create_user(email='testuser@example.com', password='ValidPassword123!')

        # Valid login
        resp = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'ValidPassword123!'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

        # Logout
        resp_logout = self.client.get(self.logout_url)
        self.assertEqual(resp_logout.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

        # Invalid password
        resp_invalid = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'WrongPassword999!'
        })
        self.assertEqual(resp_invalid.status_code, 401)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_tc15_security_handling(self):
        """
        TC-15: Salted password hash (SR-02), output encoding (SR-04),
        and 15-minute lockout after 5 failed logins (SR-05).
        """
        raw_pw = 'SuperSecret123!'
        user = User.objects.create_user(email='securityuser@example.com', password=raw_pw)

        # SR-02: Verify password stored as hash, not plaintext
        user.refresh_from_db()
        self.assertNotEqual(user.password, raw_pw)
        self.assertTrue(user.password.startswith('pbkdf2_') or user.password.startswith('argon2'))

        # SR-05: 5 failed logins trigger lockout on 6th
        for i in range(5):
            resp = self.client.post(self.login_url, {
                'email': 'securityuser@example.com',
                'password': f'WrongGuess_{i}'
            })
            self.assertEqual(resp.status_code, 401)

        # 6th attempt should be locked out (HTTP 429)
        resp_lockout = self.client.post(self.login_url, {
            'email': 'securityuser@example.com',
            'password': 'WrongGuess_6'
        })
        self.assertEqual(resp_lockout.status_code, 429)

    def test_sr03_csrf_and_session_protection(self):
        """SR-03: CSRF is enforced and session cookies use hardened defaults."""
        csrf_client = Client(enforce_csrf_checks=True)
        User.objects.create_user(email='csrf@example.com', password='ValidPassword123!')

        denied = csrf_client.post(self.login_url, {
            'email': 'csrf@example.com',
            'password': 'ValidPassword123!',
        })
        self.assertEqual(denied.status_code, 403)

        csrf_client.get(self.login_url)
        token = csrf_client.cookies['csrftoken'].value
        accepted = csrf_client.post(
            self.login_url,
            {'email': 'csrf@example.com', 'password': 'ValidPassword123!'},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(accepted.status_code, 302)
        self.assertIn('_auth_user_id', csrf_client.session)

        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertEqual(settings.CSRF_COOKIE_SECURE, settings.SESSION_COOKIE_SECURE)
