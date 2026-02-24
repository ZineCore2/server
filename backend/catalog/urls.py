from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"zines", views.ZineViewSet, basename="zine")
router.register(r"vocabularies/subjects", views.SubjectViewSet, basename="subject")
router.register(r"vocabularies/genres", views.GenreViewSet, basename="genre")
router.register(
    r"vocabularies/rights-statements",
    views.RightsStatementViewSet,
    basename="rights-statement",
)
router.register(
    r"vocabularies/languages",
    views.LanguageViewSet,
    basename="language",
)

urlpatterns = router.urls
