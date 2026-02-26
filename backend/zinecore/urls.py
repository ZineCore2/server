from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

from core.admin_views import ImportJSONView

urlpatterns = [
    path("admin/import-json/", ImportJSONView.as_view(), name="import_json"),
    path("admin/", admin.site.urls),
    path("api/", include("catalog.urls")),
    path("api/", include("agents.urls")),
    path("api/", include("repositories.urls")),
    path("api/", include("geography.urls")),
    path("api/", include("holdings.urls")),
    path("api/", include("core.urls")),
    path("api/auth/", include("rest_framework.urls")),
    path("api/auth/token/", obtain_auth_token, name="api-token-auth"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
