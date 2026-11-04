from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Django's built-in login/logout views (logout is POST only).
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("hiring.urls")),
]
