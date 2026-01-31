from __future__ import annotations

from abc import ABC, abstractmethod


class PersonaInterface(ABC):
    @property
    @abstractmethod
    def key(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def title(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def prompt(self) -> str:
        raise NotImplementedError

    def build_system_prompt(self) -> str:
        return f"Persona: {self.title}\nInstructions: {self.prompt}"
