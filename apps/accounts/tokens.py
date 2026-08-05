from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Generates and validates email verification tokens.
    """

    def _make_hash_value(self, user, timestamp):
        """
        Includes the user's verification status in the hash.

        once the user verifies their email, the token automatically becomes invalid.
        """
        return f"{user.pk}{timestamp}{user.is_email_verified}"


email_verification_token = EmailVerificationTokenGenerator()


password_reset_token = PasswordResetTokenGenerator()
