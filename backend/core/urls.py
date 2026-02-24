from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r"vocabularies/external-id-systems",
    views.ExternalIdSystemViewSet,
    basename="external-id-system",
)
router.register(
    r"vocabularies/external-uri-types",
    views.ExternalUriTypeViewSet,
    basename="external-uri-type",
)

urlpatterns = router.urls
