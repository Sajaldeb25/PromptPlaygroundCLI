"""Groq API adapter — no printing or file I/O."""

from prompt_playground.models import ChatSettings


class ChatService:
    def __init__(self, client, settings: ChatSettings):
        self._client = client
        self._settings = settings

    def send(self, user_input: str) -> tuple[str | None, int, str | None]:
        """Send a prompt to the API.

        Returns:
            (response_text, token_count, error_message)
            On success error_message is None; on failure response_text is None.
        """
        messages = []
        if self._settings.system_prompt:
            messages.append({"role": "system", "content": self._settings.system_prompt})
        messages.append({"role": "user", "content": user_input})

        try:
            response = self._client.chat.completions.create(
                model=self._settings.model,
                messages=messages,
                temperature=self._settings.temperature,
                max_tokens=self._settings.max_tokens,
            )
        except Exception as exc:
            return None, 0, str(exc)

        text = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return text, tokens, None
