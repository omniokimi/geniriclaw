"""Multi-agent architecture: supervisor, bus, and inter-agent communication."""

from geniriclaw.multiagent.bus import InterAgentBus
from geniriclaw.multiagent.health import AgentHealth
from geniriclaw.multiagent.models import SubAgentConfig
from geniriclaw.multiagent.supervisor import AgentSupervisor

__all__ = ["AgentHealth", "AgentSupervisor", "InterAgentBus", "SubAgentConfig"]
