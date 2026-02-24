from agents.models import Agent
from catalog.models import Zine
from holdings.models import Holding
from repositories.models import Repository


def dashboard_callback(request, context):
    """Add metric counts to dashboard context."""
    context.update({
        'zine_count': Zine.objects.count(),
        'agent_count': Agent.objects.count(),
        'repository_count': Repository.objects.count(),
        'holding_count': Holding.objects.count(),
    })
    return context
