"""Custom middleware for Karteikarten application."""
from django.shortcuts import redirect
from django.urls import reverse


class PasswordChangeRequiredMiddleware:
    """Middleware that forces users to change their password if required."""

    # URLs that are always allowed (without password change)
    ALLOWED_URLS = [
        'passwort_aendern',
        'logout',
        'login',
        'manifest',
        'service_worker',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if user needs to change password
            try:
                from .models import BenutzerStatistik
                stats = BenutzerStatistik.get_or_create_for_user(request.user)

                if stats.muss_passwort_aendern:
                    # Check if current URL is allowed
                    if request.resolver_match:
                        url_name = request.resolver_match.url_name
                        if url_name not in self.ALLOWED_URLS:
                            return redirect('passwort_aendern')
            except Exception:
                pass  # If anything fails, just continue

        return self.get_response(request)
