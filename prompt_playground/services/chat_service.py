"""Groq API adapter — no printing or file I/O."""

from collections.abc import Iterator
from dataclasses import dataclass

from prompt_playground.config import COT_SYSTEM_PROMPT
from prompt_playground.models import ChatSettings


@dataclass
class StreamResult:
    """Mutable container filled while consuming send_stream() deltas."""

    tokens: int = 0
    error: str | None = None


class ChatService:
    def __init__(self, client, settings: ChatSettings):
        self._client = client
        self._settings = settings

    def _build_messages(self, user_input: str) -> list[dict]:
        messages = []
        system_parts = []

        if self._settings.system_prompt:
            system_parts.append(self._settings.system_prompt.strip())
        if self._settings.cot_enabled:
            system_parts.append(COT_SYSTEM_PROMPT.strip())

        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        messages.append({"role": "user", "content": user_input})
        return messages

    def _completion_kwargs(self, messages: list[dict]) -> dict:
        return {
            "model": self._settings.model,
            "messages": messages,
            "temperature": self._settings.temperature,
            "max_tokens": self._settings.max_tokens,
        }

    def send(self, user_input: str) -> tuple[str | None, int, str | None]:
        """Send a prompt to the API (blocking).

        Returns:
            (response_text, token_count, error_message)
            On success error_message is None; on failure response_text is None.
        """
        messages = self._build_messages(user_input)

        try:
            response = self._client.chat.completions.create(**self._completion_kwargs(messages))
        except Exception as exc:
            return None, 0, str(exc)

        text = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return text, tokens, None

    def send_stream(self, user_input: str) -> tuple[Iterator[str], StreamResult]:
        """Stream a prompt to the API token-by-token.

        Returns:
            (delta_iterator, stream_result)
            Iterate deltas for text chunks. After iteration, read stream_result.tokens
            and stream_result.error (set if the request fails before streaming).
        """
        stream_result = StreamResult()
        messages = self._build_messages(user_input)

        def generate() -> Iterator[str]:
            try:
                stream = self._client.chat.completions.create(
                    **self._completion_kwargs(messages),
                    stream=True,
                    stream_options={"include_usage": True},
                )
            except Exception as exc:
                stream_result.error = str(exc)
                return

            for chunk in stream:
                if chunk.choices:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                if chunk.usage and chunk.usage.total_tokens:
                    stream_result.tokens = chunk.usage.total_tokens

        return generate(), stream_result
