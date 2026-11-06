from django.shortcuts import render


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
