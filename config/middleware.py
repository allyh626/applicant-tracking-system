from urllib.parse import urlsplit

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import render, resolve_url

SESSION_MARKER_COOKIE = "was_logged_in"
SESSION_ENDED_MESSAGE = "Your session ended, so you were logged out. Log in again to continue."


class SessionEndedMessageMiddleware:
    """Tell someone why they're on the login page when their session ended.

    The server can't tell a session that ended from someone who never logged
    in, so the browser keeps a small marker cookie while logged in. Logging out
    removes it. A request with the marker but no login means the session ended
    some other way (it expired, or was removed), so the login page says so.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Checked before the view runs, so a logout request still counts as logged in.
        was_logged_in = request.user.is_authenticated
        response = self.get_response(request)
        # A value, not just the name: a deleted cookie can linger with an empty one.
        has_marker = bool(request.COOKIES.get(SESSION_MARKER_COOKIE))
        if request.user.is_authenticated:
            if not has_marker:
                response.set_cookie(
                    SESSION_MARKER_COOKIE,
                    "1",
                    max_age=settings.SESSION_COOKIE_AGE,
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=True,
                    samesite="Lax",
                )
        elif has_marker:
            # Logged in before, not logged out, and no session now. Only on the
            # redirect to login: a message shows on the page after this one,
            # which for a redirect is the login page itself.
            if not was_logged_in and response.status_code == 302:
                messages.info(request, SESSION_ENDED_MESSAGE)
            # Either way the marker's job is done: a logout, or the message is shown.
            response.delete_cookie(SESSION_MARKER_COOKIE, samesite="Lax")
        return response


class HtmxLoginRedirectMiddleware:
    """Send a logged-out HTMX click to the login page as a whole page.

    When a session has expired, LoginRequiredMiddleware answers with a redirect
    to the login page. HTMX would follow it quietly and swap the whole login
    page into the table row. For HTMX requests this sends an HX-Redirect header
    instead, which makes HTMX load the login page in the browser properly.

    After logging in, the user goes back to the page they were on (HTMX sends
    it as HX-Current-URL), not to the button's POST-only URL.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            request.headers.get("HX-Request")
            and not request.user.is_authenticated
            and response.status_code == 302
        ):
            current = urlsplit(request.headers.get("HX-Current-URL", ""))
            if current.path:
                page = current.path + (f"?{current.query}" if current.query else "")
                login_url = redirect_to_login(page)["Location"]
            else:
                login_url = resolve_url(settings.LOGIN_URL)
            replacement = HttpResponse()
            replacement["HX-Redirect"] = login_url
            # Keep the cookies the redirect carried, such as the "session ended" message.
            replacement.cookies = response.cookies
            return replacement
        return response


class FriendlyMethodNotAllowedMiddleware:
    """Give Django's empty 405 responses a page a person can read.

    POST-only views (logout, close/reopen, and later archive, restore and stage
    moves) answer a GET with an empty 405, which a browser shows as a blank
    screen. This keeps the 405 status and Allow header but adds the normal
    layout and a short explanation. HTMX requests are left alone, since they
    expect a fragment, not a whole page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            response.status_code == 405
            and not response.content
            and not request.headers.get("HX-Request")
        ):
            friendly = render(request, "405.html", status=405)
            friendly["Allow"] = response.get("Allow", "")
            return friendly
        return response
