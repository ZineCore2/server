from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"repositories", views.RepositoryViewSet, basename="repository")
router.register(r"vocabularies/repo-kinds", views.RepoKindViewSet, basename="repo-kind")

urlpatterns = router.urls
