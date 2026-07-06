"""Application orchestrator — wires services and runs the REPL."""

import os
import sys

from colorama import Fore, Style, init
from dotenv import load_dotenv
from groq import Groq

from prompt_playground.cli.commands import CommandHandler
from prompt_playground.cli.settings_ui import SettingsUI
from prompt_playground.config import DEFAULT_MODEL, ENV_FILE, LOGS_FILE, TEMPLATES_FILE
from prompt_playground.models import ChatSettings, SessionState
from prompt_playground.services.chat_service import ChatService
from prompt_playground.services.log_service import LogService
from prompt_playground.services.template_service import TemplateService
from prompt_playground.storage.log_store import LogStore
from prompt_playground.storage.template_store import TemplateStore

init(autoreset=True)


class PromptPlaygroundApp:
    def __init__(self):
        load_dotenv(ENV_FILE) # Load environment variables from .env file

        api_key = os.getenv("GROQ_API_KEY") # API key from ENV file
        if not api_key:
            print(f"{Fore.RED}Error: GROQ_API_KEY not set. Copy .env.example to .env and add your key.")
            sys.exit(1)

        self.settings = ChatSettings(model=DEFAULT_MODEL)
        self.session = SessionState()

        # Initialize storage and services
        # It is not directly used by user,
        # but it is used by services to store and retrieve data
        template_store = TemplateStore(TEMPLATES_FILE)
        log_store = LogStore(LOGS_FILE)

        self.template_svc = TemplateService(template_store)
        self.log_svc = LogService(log_store)

        client = Groq(api_key=api_key)
        self.chat_svc = ChatService(client, self.settings)

        self.command_handler = CommandHandler(
            template_svc=self.template_svc,
            log_svc=self.log_svc,
            settings=self.settings,
            session=self.session,
            settings_ui=SettingsUI(),
        )

    def run(self) -> None:
        """
        Execute the REPL loop
        Execute when used PromptPlaygroundApp().run()
        """

        print(f"{Style.BRIGHT}Prompt Playground v1.0")
        print("Type /help for commands\n")

        try:
            # REPL loop, always running until user give /exit command or Ctrl+C
            while True:
                user_input = input(f"{Fore.CYAN}You: {Style.RESET_ALL}").strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if self.command_handler.handle(user_input):
                        break
                    continue

                response, tokens, error = self.chat_svc.send(user_input)
                if error:
                    print(f"{Fore.RED}API error: {error}")
                    continue

                print(f"{Fore.GREEN}AI: {response}")
                print(f"{Fore.YELLOW}   Tokens: {tokens} | Model: {self.settings.model}")

                self.session.current_prompt = user_input
                entry = self.log_svc.build_entry(
                    user=user_input,
                    response=response,
                    tokens=tokens,
                    template=self.session.current_template,
                    settings=self.settings,
                )
                self.log_svc.add(entry)
        except KeyboardInterrupt:
            print(f"\n{Fore.GREEN}Goodbye!")
