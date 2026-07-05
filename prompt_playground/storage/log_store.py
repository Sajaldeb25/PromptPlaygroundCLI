"""Repository for logs.json persistence and export files."""

import csv
import json
from pathlib import Path


LOG_FIELDNAMES = [
    "timestamp",
    "template",
    "user",
    "response",
    "model",
    "tokens",
    "temperature",
]


class LogStore:
    def __init__(self, file_path: Path):
        self._file_path = file_path

    def load(self) -> list[dict]:
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            from colorama import Fore

            print(f"{Fore.RED}Error: {self._file_path} contains invalid JSON.")
            return []

    def save(self, logs: list[dict]) -> None:
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)

    def export_json(self, logs: list[dict], filename: Path) -> Path:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
        return filename

    def export_csv(self, logs: list[dict], filename: Path) -> Path:
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES)
            writer.writeheader()
            writer.writerows(logs)
        return filename
