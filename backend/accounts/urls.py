from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"profiles", views.ProfileViewSet, basename="profile")
router.register(r"submissions", views.ZineSubmissionViewSet, basename="submission")
router.register(
    r"vocabularies/submission-statuses",
    views.SubmissionStatusViewSet,
    basename="submission-status",
)

urlpatterns = router.urls
