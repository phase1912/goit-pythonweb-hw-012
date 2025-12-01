"""
Constants for integration tests.
"""


class Urls:
    """API endpoint URLs."""

    # Root endpoints
    ROOT = "/"
    HEALTHCHECK = "/health"

    # Auth endpoints
    AUTH_REGISTER = "/auth/register"
    AUTH_LOGIN = "/auth/login"
    AUTH_LOGOUT = "/auth/logout"
    AUTH_REFRESH = "/auth/refresh"
    AUTH_ME = "/auth/me"
    AUTH_VERIFY_EMAIL = "/auth/verify-email/{token}"
    AUTH_RESEND_VERIFICATION = "/auth/resend-verification"
    AUTH_AVATAR = "/auth/avatar"
    AUTH_RESET_PASSWORD_REQUEST = "/auth/reset-password-request"
    AUTH_RESET_PASSWORD = "/auth/reset-password/{token}"
    AUTH_RESET_PASSWORD_CONFIRM = "/auth/reset-password-confirm"

    # Contact endpoints
    CONTACTS = "/contacts/"
    CONTACT_DETAIL = "/contacts/{id}"
    CONTACTS_SEARCH = "/contacts/search"
    CONTACTS_BIRTHDAYS = "/contacts/birthdays"

