"""Domain models for session and chat settings."""

from dataclasses import dataclass


@dataclass
class ChatSettings:
    model: str
    temperature: float = 0.7
    max_tokens: int = 500
    system_prompt: str = ""


@dataclass
class SessionState:
    current_prompt: str = ""
    current_template: str | None = None
