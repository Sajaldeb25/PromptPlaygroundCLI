"""Repository for templates.json persistence."""

import json
from pathlib import Path

from colorama import Fore


class TemplateStore:
    def __init__(self, file_path: Path):
        self._file_path = file_path

    def load(self) -> dict[str, str]:
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: {self._file_path} contains invalid JSON.")
            return {}

    def save(self, templates: dict[str, str]) -> None:
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(templates, f, indent=2)
