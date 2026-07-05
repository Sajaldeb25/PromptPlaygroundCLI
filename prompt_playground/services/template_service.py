"""Template business logic using TemplateStore."""

from prompt_playground.storage.template_store import TemplateStore


class TemplateService:
    def __init__(self, store: TemplateStore):
        self._store = store
        self._templates: dict[str, str] = store.load()

    def save(self, name: str, prompt: str) -> bool:
        name = name.strip()
        prompt = prompt.strip()
        if not name or not prompt:
            return False

        self._templates[name] = prompt
        self._store.save(self._templates)
        return True

    def load(self, name: str) -> str | None:
        name = name.strip()
        return self._templates.get(name)

    def list_all(self) -> dict[str, str]:
        return dict(self._templates)

    def delete(self, name: str) -> bool:
        name = name.strip()
        if name not in self._templates:
            return False

        del self._templates[name]
        self._store.save(self._templates)
        return True
