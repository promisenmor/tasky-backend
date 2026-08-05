from rest_framework.throttling import AnonRateThrottle


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class RegisterThrottle(AnonRateThrottle):
    scope = "register"


class ForgotPasswordThrottle(AnonRateThrottle):
    scope = "forgot_password"


class ResendVerificationRateThrottle(AnonRateThrottle):
    scope = "resend_verification"
