"""Application constants and configuration paths."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
BASE_DIR = PACKAGE_DIR.parent

TEMPLATES_FILE = BASE_DIR / "templates.json"
LOGS_FILE = BASE_DIR / "logs.json"
ENV_FILE = BASE_DIR / ".env"

MODELS = {
    "mixtral": "qwen/qwen3-32b",
    "llama2": "llama-3.3-70b-versatile",
    "gemma": "llama-3.1-8b-instant",
}

DEFAULT_MODEL = MODELS["llama2"]

HELP_TEXT = """
Available commands:
  /save <name>    Save last prompt as template
  /load <name>    Load template (preview only)
  /list           List all templates
  /delete <name>  Delete a template
  /history        Show recent interactions
  /export         Export logs to JSON or CSV
  /config         Change model, temperature, tokens, system prompt
  /help           Show this help
  /exit           Exit playground
"""
