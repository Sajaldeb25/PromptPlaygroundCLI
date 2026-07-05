"""Slash command dispatcher."""

from colorama import Fore

from prompt_playground.cli.settings_ui import SettingsUI
from prompt_playground.config import HELP_TEXT
from prompt_playground.models import ChatSettings, SessionState
from prompt_playground.services.log_service import LogService
from prompt_playground.services.template_service import TemplateService


class CommandHandler:
    def __init__(
        self,
        template_svc: TemplateService,
        log_svc: LogService,
        settings: ChatSettings,
        session: SessionState,
        settings_ui: SettingsUI | None = None,
    ):
        self._template_svc = template_svc
        self._log_svc = log_svc
        self._settings = settings
        self._session = session
        self._settings_ui = settings_ui or SettingsUI()

    def handle(self, line: str) -> bool:
        """Parse and run a slash command. Returns True to exit."""
        parts = line.strip().split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if command == "/help":
            print(HELP_TEXT)
        elif command == "/save":
            self._handle_save(arg)
        elif command == "/load":
            self._handle_load(arg)
        elif command == "/list":
            self._handle_list()
        elif command == "/delete":
            self._handle_delete(arg)
        elif command == "/history":
            self._handle_history()
        elif command == "/export":
            self._handle_export()
        elif command == "/config":
            self._settings_ui.prompt(self._settings)
        elif command == "/exit":
            print(f"{Fore.GREEN}Goodbye!")
            return True
        else:
            print(f"{Fore.RED}Unknown command: {command}. Type /help for available commands.")
        return False

    def _handle_save(self, name: str) -> None:
        if not name:
            print(f"{Fore.RED}Usage: /save <name>")
            return
        if not name.strip():
            print(f"{Fore.RED}Error: template name cannot be empty.")
            return
        if not self._session.current_prompt.strip():
            print(f"{Fore.RED}Error: no prompt to save. Send a message first.")
            return
        if self._template_svc.save(name, self._session.current_prompt):
            print(f'{Fore.GREEN}Saved as "{name.strip()}"')

    def _handle_load(self, name: str) -> None:
        if not name:
            print(f"{Fore.RED}Usage: /load <name>")
            return
        prompt = self._template_svc.load(name)
        if prompt is None:
            print(f'{Fore.RED}Error: template "{name.strip()}" not found.')
            return
        self._session.current_template = name.strip()
        preview = prompt if len(prompt) <= 80 else prompt[:77] + "..."
        print(f'{Fore.GREEN}Loaded "{name.strip()}": {preview}')

    def _handle_list(self) -> None:
        templates = self._template_svc.list_all()
        if not templates:
            print(f"{Fore.YELLOW}No templates saved yet.")
            return
        print(f"{Fore.CYAN}Saved templates:")
        for i, (name, prompt) in enumerate(templates.items(), start=1):
            preview = prompt if len(prompt) <= 60 else prompt[:57] + "..."
            print(f"  {i}. {name}: {preview}")

    def _handle_delete(self, name: str) -> None:
        if not name:
            print(f"{Fore.RED}Usage: /delete <name>")
            return
        if not self._template_svc.delete(name):
            print(f'{Fore.RED}Error: template "{name.strip()}" not found.')
            return
        if self._session.current_template == name.strip():
            self._session.current_template = None
        print(f'{Fore.GREEN}Deleted template "{name.strip()}"')

    def _handle_history(self) -> None:
        entries = self._log_svc.recent()
        if not entries:
            print(f"{Fore.YELLOW}No interactions logged yet.")
            return
        print(f"{Fore.CYAN}Recent interactions:")
        for entry in entries:
            ts = entry.get("timestamp", "")
            time_part = ts[11:16] if len(ts) >= 16 else ts
            template = entry.get("template") or "—"
            response = entry.get("response", "")
            preview = response if len(response) <= 40 else response[:37] + "..."
            print(f'  [{time_part}] {template} -> "{preview}"')

    def _handle_export(self) -> None:
        if not self._log_svc.has_logs():
            print(f"{Fore.YELLOW}No logs to export.")
            return
        fmt = input("Export format (json/csv) [json]: ").strip().lower() or "json"
        path = self._log_svc.export(fmt)
        if path:
            print(f"{Fore.GREEN}Logs exported to {path}")
