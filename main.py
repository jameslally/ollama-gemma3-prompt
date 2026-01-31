from __future__ import annotations

from typing import Dict, List

from ollama import chat
from ollama import ChatResponse

from persona.factory import get_persona
from persona.interface import PersonaInterface

Message = Dict[str, str]


def build_messages(persona: PersonaInterface, chat_history: List[Message]) -> List[Message]:
    system_prompt = persona.build_system_prompt()
    return [{"role": "system", "content": system_prompt}] + chat_history


def generate_response(model: str, persona: PersonaInterface, chat_history: List[Message]) -> str:
    response: ChatResponse = chat(model=model, messages=build_messages(persona, chat_history))
    return response.message.content


if __name__ == "__main__":
    # CLI usage: type prompts, get model responses.
    persona = get_persona("parent")
    history: List[Message] = []
    model = "gemma3"

    print("Persona: Human Parent of a Child")
    print("Type your message. Press Enter on an empty line to exit.")

    while True:
        user_input = input("> ").strip()
        if not user_input:
            break
        history.append({"role": "user", "content": user_input})
        assistant_reply = generate_response(model=model, persona=persona, chat_history=history)
        history.append({"role": "assistant", "content": assistant_reply})
        print(assistant_reply)