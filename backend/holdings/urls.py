from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"holdings", views.HoldingViewSet, basename="holding")
router.register(
    r"vocabularies/access-statuses", views.AccessStatusViewSet, basename="access-status"
)
router.register(
    r"vocabularies/distro-statuses", views.DistroStatusViewSet, basename="distro-status"
)

urlpatterns = router.urls
