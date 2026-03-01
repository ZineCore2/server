from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"profiles", views.ProfileViewSet, basename="profile")
router.register(r"agent-claims", views.ProfileAgentClaimViewSet, basename="agent-claim")
router.register(r"repository-claims", views.ProfileRepositoryClaimViewSet, basename="repository-claim")
router.register(r"submissions", views.ZineSubmissionViewSet, basename="submission")
router.register(
    r"vocabularies/submission-statuses",
    views.SubmissionStatusViewSet,
    basename="submission-status",
)

urlpatterns = [
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
] + router.urls
