"""Prompt Playground CLI — experiment with prompts, templates, and result logging."""

import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from colorama import Fore, Style, init
from dotenv import load_dotenv
from groq import Groq

init(autoreset=True)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_FILE = BASE_DIR / "templates.json"
LOGS_FILE = BASE_DIR / "logs.json"

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


class PromptPlayground:
    def __init__(self):
        load_dotenv(BASE_DIR / ".env")

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print(f"{Fore.RED}Error: GROQ_API_KEY not set. Copy .env.example to .env and add your key.")
            sys.exit(1)

        self.client = Groq(api_key=api_key)
        self.model = DEFAULT_MODEL
        self.temperature = 0.7
        self.max_tokens = 500
        self.system_prompt = ""
        self.current_prompt = ""
        self.current_template = None

        self.templates = self.load_templates()
        self.logs = self.load_logs()

    def load_templates(self) -> dict:
        try:
            with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: {TEMPLATES_FILE} contains invalid JSON.")
            return {}

    def load_logs(self) -> list:
        try:
            with open(LOGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: {LOGS_FILE} contains invalid JSON.")
            return []

    def save_templates_to_disk(self) -> None:
        with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.templates, f, indent=2)

    def save_logs_to_disk(self) -> None:
        with open(LOGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2)

    def chat(self, user_input: str) -> tuple[str | None, int]:
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as exc:
            print(f"{Fore.RED}API error: {exc}")
            return None, 0

        text = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return text, tokens

    def save_template(self, name: str, prompt: str) -> bool:
        name = name.strip()
        prompt = prompt.strip()
        if not name:
            print(f"{Fore.RED}Error: template name cannot be empty.")
            return False
        if not prompt:
            print(f"{Fore.RED}Error: no prompt to save. Send a message first.")
            return False

        self.templates[name] = prompt
        self.save_templates_to_disk()
        print(f'{Fore.GREEN}Saved as "{name}"')
        return True

    def load_template(self, name: str) -> str | None:
        name = name.strip()
        if name not in self.templates:
            print(f'{Fore.RED}Error: template "{name}" not found.')
            return None

        prompt = self.templates[name]
        self.current_template = name
        preview = prompt if len(prompt) <= 80 else prompt[:77] + "..."
        print(f'{Fore.GREEN}Loaded "{name}": {preview}')
        return prompt

    def list_templates(self) -> None:
        if not self.templates:
            print(f"{Fore.YELLOW}No templates saved yet.")
            return

        print(f"{Fore.CYAN}Saved templates:")
        for i, (name, prompt) in enumerate(self.templates.items(), start=1):
            preview = prompt if len(prompt) <= 60 else prompt[:57] + "..."
            print(f"  {i}. {name}: {preview}")

    def delete_template(self, name: str) -> bool:
        name = name.strip()
        if name not in self.templates:
            print(f'{Fore.RED}Error: template "{name}" not found.')
            return False

        del self.templates[name]
        self.save_templates_to_disk()
        if self.current_template == name:
            self.current_template = None
        print(f'{Fore.GREEN}Deleted template "{name}"')
        return True

    def log_result(self, user: str, response: str, tokens: int) -> None:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "template": self.current_template,
            "user": user,
            "response": response,
            "model": self.model,
            "tokens": tokens,
            "temperature": self.temperature,
        }
        self.logs.append(entry)
        self.save_logs_to_disk()

    def view_history(self, limit: int = 10) -> None:
        if not self.logs:
            print(f"{Fore.YELLOW}No interactions logged yet.")
            return

        print(f"{Fore.CYAN}Recent interactions:")
        for entry in self.logs[-limit:]:
            ts = entry.get("timestamp", "")
            time_part = ts[11:16] if len(ts) >= 16 else ts
            template = entry.get("template") or "—"
            response = entry.get("response", "")
            preview = response if len(response) <= 40 else response[:37] + "..."
            print(f"  [{time_part}] {template} -> \"{preview}\"")

    def export_logs(self) -> None:
        if not self.logs:
            print(f"{Fore.YELLOW}No logs to export.")
            return

        fmt = input("Export format (json/csv) [json]: ").strip().lower() or "json"
        date_str = datetime.now().strftime("%Y-%m-%d")

        if fmt == "csv":
            filename = BASE_DIR / f"logs_{date_str}.csv"
            fieldnames = [
                "timestamp",
                "template",
                "user",
                "response",
                "model",
                "tokens",
                "temperature",
            ]
            with open(filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.logs)
        else:
            filename = BASE_DIR / f"logs_{date_str}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.logs, f, indent=2)

        print(f"{Fore.GREEN}Logs exported to {filename}")

    def update_settings(self) -> None:
        print(f"{Fore.CYAN}Current settings:")
        model_key = next((k for k, v in MODELS.items() if v == self.model), self.model)
        print(f"  Model: {model_key} ({self.model})")
        print(f"  Temperature: {self.temperature}")
        print(f"  Max tokens: {self.max_tokens}")
        print(f"  System prompt: {self.system_prompt or '(none)'}")

        print(f"\n{Fore.CYAN}Models: 1=mixtral  2=llama2  3=gemma  (or type key name)")
        choice = input("Model [Enter to keep]: ").strip().lower()
        if choice:
            mapping = {"1": "mixtral", "2": "llama2", "3": "gemma"}
            key = mapping.get(choice, choice)
            if key in MODELS:
                self.model = MODELS[key]
                print(f"{Fore.GREEN}Model set to {key} ({self.model})")
            else:
                print(f"{Fore.RED}Unknown model. Keeping {self.model}")

        temp_input = input("Temperature 0.0-2.0 [Enter to keep]: ").strip()
        if temp_input:
            try:
                temp = float(temp_input)
                if 0.0 <= temp <= 2.0:
                    self.temperature = temp
                    print(f"{Fore.GREEN}Temperature set to {self.temperature}")
                else:
                    print(f"{Fore.RED}Temperature must be between 0.0 and 2.0.")
            except ValueError:
                print(f"{Fore.RED}Invalid temperature. Keeping {self.temperature}")

        tokens_input = input("Max tokens [Enter to keep]: ").strip()
        if tokens_input:
            try:
                tokens = int(tokens_input)
                if tokens > 0:
                    self.max_tokens = tokens
                    print(f"{Fore.GREEN}Max tokens set to {self.max_tokens}")
                else:
                    print(f"{Fore.RED}Max tokens must be a positive integer.")
            except ValueError:
                print(f"{Fore.RED}Invalid max tokens. Keeping {self.max_tokens}")

        system_input = input("System prompt [Enter to keep, type 'clear' to remove]: ").strip()
        if system_input == "clear":
            self.system_prompt = ""
            print(f"{Fore.GREEN}System prompt cleared.")
        elif system_input:
            self.system_prompt = system_input
            print(f"{Fore.GREEN}System prompt updated.")

    def handle_command(self, line: str) -> bool:
        """Parse and run a slash command. Returns True to exit."""
        parts = line.strip().split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if command == "/help":
            print(HELP_TEXT)
        elif command == "/save":
            if not arg:
                print(f"{Fore.RED}Usage: /save <name>")
            else:
                self.save_template(arg, self.current_prompt)
        elif command == "/load":
            if not arg:
                print(f"{Fore.RED}Usage: /load <name>")
            else:
                self.load_template(arg)
        elif command == "/list":
            self.list_templates()
        elif command == "/delete":
            if not arg:
                print(f"{Fore.RED}Usage: /delete <name>")
            else:
                self.delete_template(arg)
        elif command == "/history":
            self.view_history()
        elif command == "/export":
            self.export_logs()
        elif command == "/config":
            self.update_settings()
        elif command == "/exit":
            print(f"{Fore.GREEN}Goodbye!")
            return True
        else:
            print(f"{Fore.RED}Unknown command: {command}. Type /help for available commands.")
        return False

    def run(self) -> None:
        print(f"{Style.BRIGHT}Prompt Playground v1.0")
        print("Type /help for commands\n")

        try:
            while True:
                user_input = input(f"{Fore.CYAN}You: {Style.RESET_ALL}").strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if self.handle_command(user_input):
                        break
                    continue

                response, tokens = self.chat(user_input)
                if response is None:
                    continue

                print(f"{Fore.GREEN}AI: {response}")
                print(f"{Fore.YELLOW}   Tokens: {tokens} | Model: {self.model}")

                self.current_prompt = user_input
                self.log_result(user_input, response, tokens)
        except KeyboardInterrupt:
            print(f"\n{Fore.GREEN}Goodbye!")


if __name__ == "__main__":
    app = PromptPlayground()
    app.run()
