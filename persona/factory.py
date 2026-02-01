from __future__ import annotations

from typing import Dict

from persona.interface import PersonaInterface
from persona.educator import EducatorPersona
from persona.parent import ParentOfChildPersona


PERSONAS: Dict[str, PersonaInterface] = {
    "educator": EducatorPersona(),
    "parent": ParentOfChildPersona(),
        }


def get_persona(persona_key: str) -> PersonaInterface:
    if persona_key not in PERSONAS:
        raise ValueError(f"Unknown persona: {persona_key}")
    return PERSONAS[persona_key]
