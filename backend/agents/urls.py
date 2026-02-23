from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"agents", views.AgentViewSet, basename="agent")
router.register(r"vocabularies/agent-kinds", views.AgentKindViewSet, basename="agent-kind")
router.register(r"vocabularies/agent-roles", views.AgentRoleViewSet, basename="agent-role")

urlpatterns = router.urls
