"""Interaction log business logic using LogStore."""

from datetime import datetime
from pathlib import Path

from prompt_playground.config import BASE_DIR
from prompt_playground.models import ChatSettings
from prompt_playground.storage.log_store import LogStore


class LogService:
    def __init__(self, store: LogStore):
        self._store = store
        self._logs: list[dict] = store.load()

    def add(
        self,
        entry: dict,
    ) -> None:
        self._logs.append(entry)
        self._store.save(self._logs)

    def build_entry(
        self,
        user: str,
        response: str,
        tokens: int,
        template: str | None,
        settings: ChatSettings,
        thinking: str | None = None,
        answer: str | None = None,
    ) -> dict:
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "template": template,
            "user": user,
            "response": response,
            "thinking": thinking,
            "answer": answer,
            "model": settings.model,
            "tokens": tokens,
            "temperature": settings.temperature,
            "cot_enabled": settings.cot_enabled,
            "stream_enabled": settings.stream_enabled,
        }

    def recent(self, limit: int = 10) -> list[dict]:
        return self._logs[-limit:]

    def has_logs(self) -> bool:
        return bool(self._logs)

    def export(self, fmt: str) -> Path | None:
        if not self._logs:
            return None

        date_str = datetime.now().strftime("%Y-%m-%d")
        if fmt == "csv":
            filename = BASE_DIR / f"logs_{date_str}.csv"
            return self._store.export_csv(self._logs, filename)

        filename = BASE_DIR / f"logs_{date_str}.json"
        return self._store.export_json(self._logs, filename)
