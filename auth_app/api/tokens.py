from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AppTokenGenerator(PasswordResetTokenGenerator):
    """Token for email activation - invalidates when is_active changes."""
    def _make_hash_value(self, user, timestamp):
        return f"{user.is_active}{user.pk}{timestamp}"


class PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    """Token for password reset - invalidates when password changes."""
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.password}{timestamp}"


generate_token = AppTokenGenerator()
password_reset_token = PasswordResetTokenGenerator()