from .base import BasePersona
from .ceo import CEOPersona
from .chro import CHROPersona
from .eb_regional_manager import EBRegionalManagerPersona

PERSONA_REGISTRY: dict[str, type[BasePersona]] = {
    "CEO": CEOPersona,
    "CHRO": CHROPersona,
    "EB Regional Manager": EBRegionalManagerPersona,
}


def get_persona(persona_id: str) -> BasePersona:
    """Factory: return an instantiated persona by ID."""
    cls = PERSONA_REGISTRY.get(persona_id)
    if cls is None:
        raise ValueError(f"Unknown persona: {persona_id}")
    return cls()


__all__ = [
    "BasePersona",
    "CEOPersona",
    "CHROPersona",
    "EBRegionalManagerPersona",
    "PERSONA_REGISTRY",
    "get_persona",
]
