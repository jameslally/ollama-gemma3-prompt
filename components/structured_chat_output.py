from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class StructuredChatOutput:
    reply: str
    follow_up_questions: List[str]
    is_medical: bool
    is_legal: bool
    is_financial: bool
    is_not_appropriate: bool
    safety_note: Optional[str] = None

    @classmethod
    def from_json(cls, raw_json: str) -> "StructuredChatOutput":
        data = json.loads(raw_json)
        if not isinstance(data, dict):
            raise ValueError("Response JSON must be an object.")
        missing = [
            key
            for key in [
                "reply",
                "follow_up_questions",
                "is_medical",
                "is_legal",
                "is_financial",
                "is_not_appropriate",
            ]
            if key not in data
        ]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        if not isinstance(data["reply"], str):
            raise ValueError("Field 'reply' must be a string.")
        if not isinstance(data["follow_up_questions"], list) or not all(
            isinstance(item, str) for item in data["follow_up_questions"]
        ):
            raise ValueError("Field 'follow_up_questions' must be a list of strings.")
        for flag in ["is_medical", "is_legal", "is_financial", "is_not_appropriate"]:
            if not isinstance(data[flag], bool):
                raise ValueError(f"Field '{flag}' must be a boolean.")
        if "safety_note" in data and data["safety_note"] is not None and not isinstance(
            data["safety_note"], str
        ):
            raise ValueError("Field 'safety_note' must be a string or null.")
        return cls(
            reply=data["reply"],
            follow_up_questions=list(data["follow_up_questions"]),
            is_medical=data["is_medical"],
            is_legal=data["is_legal"],
            is_financial=data["is_financial"],
            is_not_appropriate=data["is_not_appropriate"],
            safety_note=data.get("safety_note"),
        )


RESPONSE_SCHEMA: Dict[str, object] = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "follow_up_questions": {"type": "array", "items": {"type": "string"}},
        "is_medical": {"type": "boolean"},
        "is_legal": {"type": "boolean"},
        "is_financial": {"type": "boolean"},
        "is_not_appropriate": {"type": "boolean"},
        "safety_note": {"type": ["string", "null"]},
    },
    "required": [
        "reply",
        "follow_up_questions",
        "is_medical",
        "is_legal",
        "is_financial",
        "is_not_appropriate",
    ],
}
