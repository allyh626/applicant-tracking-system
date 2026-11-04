from django.shortcuts import render


def dashboard(request):
    """Home page after login. A placeholder until Phase 10 builds the real dashboard."""
    return render(request, "hiring/dashboard.html")
