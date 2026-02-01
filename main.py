from __future__ import annotations

import os
from typing import Dict, List

from ollama import chat
from ollama import ChatResponse

from persona.factory import get_persona
from persona.interface import PersonaInterface
from components.rag import build_index, format_context, load_text_files, search_index
from components.structured_chat_output import RESPONSE_SCHEMA, StructuredChatOutput

Message = Dict[str, str]


def build_messages(
    persona: PersonaInterface,
    chat_history: List[Message],
    context_message: str | None = None,
) -> List[Message]:
    system_prompt = persona.build_system_prompt()
    messages: List[Message] = [{"role": "system", "content": system_prompt}]
    if context_message:
        messages.append({"role": "system", "content": context_message})
    return messages + chat_history


def generate_response(
    model: str,
    persona: PersonaInterface,
    chat_history: List[Message],
    context_message: str | None = None,
    max_retries: int = 2,
) -> StructuredChatOutput:
    messages = build_messages(persona, chat_history, context_message=context_message)
    schema_hint = (
        "Return ONLY valid JSON matching this schema: "
        "{reply:string, follow_up_questions:string[], "
        "is_medical:boolean, is_legal:boolean, is_financial:boolean, "
        "is_not_appropriate:boolean, safety_note:string|null}."
    )
    for attempt in range(max_retries + 1):
        response: ChatResponse = chat(
            model=model,
            messages=messages,
            format=RESPONSE_SCHEMA,
        )
        try:
            return StructuredChatOutput.from_json(response.message.content)
        except (ValueError, TypeError, KeyError):
            if attempt >= max_retries:
                raise
            messages = messages + [
                {
                    "role": "system",
                    "content": (
                        "The previous response did not match the required JSON schema. "
                        + schema_hint
                    ),
                }
            ]
    raise RuntimeError("Failed to produce a valid structured response.")


if __name__ == "__main__":
    # CLI usage: type prompts, get model responses.
    persona = get_persona("parent")
    history: List[Message] = []
    model = "gemma3"
    embedding_model = "embeddinggemma"
    rag_dir = "rag_docs"
    rag_index = []

    if os.path.isdir(rag_dir):
        documents = load_text_files(rag_dir, on_progress=print)
        rag_index = build_index(embedding_model, documents, on_progress=print)
        print(f"RAG: loaded {len(rag_index)} chunks from {len(documents)} files.")
    else:
        print(f"RAG: no folder found at '{rag_dir}', running without context.")

    print("Persona: Human Parent of a Child")
    print("Type your message. Press Enter on an empty line to exit.")

    while True:
        user_input = input("> ").strip()
        if not user_input:
            break
        history.append({"role": "user", "content": user_input})
        context_message = None
        if rag_index:
            top_chunks = search_index(embedding_model, rag_index, user_input, top_k=3)
            context_message = format_context(top_chunks)
        assistant_response = generate_response(
            model=model,
            persona=persona,
            chat_history=history,
            context_message=context_message,
        )
        history.append({"role": "assistant", "content": assistant_response.reply})
        print(assistant_response.reply)
        if assistant_response.follow_up_questions:
            print("Follow-up questions:")
            for question in assistant_response.follow_up_questions:
                print(f"- {question}")
        if (
            assistant_response.is_medical
            or assistant_response.is_legal
            or assistant_response.is_financial
            or assistant_response.is_not_appropriate
        ):
            print("Flags:")
            if assistant_response.is_medical:
                print("- IsMedical")
            if assistant_response.is_legal:
                print("- IsLegal")
            if assistant_response.is_financial:
                print("- IsFinancial")
            if assistant_response.is_not_appropriate:
                print("- IsNotAppropriate")
        if assistant_response.safety_note:
            print(f"Safety note: {assistant_response.safety_note}")