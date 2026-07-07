"""Interactive settings prompts for /config."""

from colorama import Fore

from prompt_playground.config import MODELS
from prompt_playground.models import ChatSettings


class SettingsUI:
    def prompt(self, settings: ChatSettings) -> ChatSettings:
        """
        when receive command /config
        Interactively update settings in place and return them.
        """
        model_key = next((k for k, v in MODELS.items() if v == settings.model), settings.model)
        print(f"{Fore.CYAN}Current settings:")
        print(f"  Model: {model_key} ({settings.model})")
        print(f"  Temperature: {settings.temperature}")
        print(f"  Max tokens: {settings.max_tokens}")
        print(f"  System prompt: {settings.system_prompt or '(none)'}")
        print(f"  Chain of thought: {'on' if settings.cot_enabled else 'off'}")
        print(f"  Streaming: {'on' if settings.stream_enabled else 'off'}")

        print(f"\n{Fore.CYAN}Models: 1=mixtral  2=llama2  3=gemma  (or type key name)")
        choice = input("Model [Enter to keep]: ").strip().lower()
        if choice:
            mapping = {"1": "mixtral", "2": "llama2", "3": "gemma"}
            key = mapping.get(choice, choice)
            if key in MODELS:
                settings.model = MODELS[key]
                print(f"{Fore.GREEN}Model set to {key} ({settings.model})")
            else:
                print(f"{Fore.RED}Unknown model. Keeping {settings.model}")

        temp_input = input("Temperature 0.0-2.0 [Enter to keep]: ").strip()
        if temp_input:
            try:
                temp = float(temp_input)
                if 0.0 <= temp <= 2.0:
                    settings.temperature = temp
                    print(f"{Fore.GREEN}Temperature set to {settings.temperature}")
                else:
                    print(f"{Fore.RED}Temperature must be between 0.0 and 2.0.")
            except ValueError:
                print(f"{Fore.RED}Invalid temperature. Keeping {settings.temperature}")

        tokens_input = input("Max tokens [Enter to keep]: ").strip()
        if tokens_input:
            try:
                tokens = int(tokens_input)
                if tokens > 0:
                    settings.max_tokens = tokens
                    print(f"{Fore.GREEN}Max tokens set to {settings.max_tokens}")
                else:
                    print(f"{Fore.RED}Max tokens must be a positive integer.")
            except ValueError:
                print(f"{Fore.RED}Invalid max tokens. Keeping {settings.max_tokens}")

        system_input = input("System prompt [Enter to keep, type 'clear' to remove]: ").strip()
        if system_input == "clear":
            settings.system_prompt = ""
            print(f"{Fore.GREEN}System prompt cleared.")
        elif system_input:
            settings.system_prompt = system_input
            print(f"{Fore.GREEN}System prompt updated.")

        cot_input = input("Chain of thought [on/off, Enter to keep]: ").strip().lower()
        if cot_input == "on":
            settings.cot_enabled = True
            print(f"{Fore.GREEN}Chain of thought enabled.")
        elif cot_input == "off":
            settings.cot_enabled = False
            print(f"{Fore.GREEN}Chain of thought disabled.")
        elif cot_input:
            print(f"{Fore.RED}Invalid value. Use on or off. Keeping {'on' if settings.cot_enabled else 'off'}.")

        stream_input = input("Streaming [on/off, Enter to keep]: ").strip().lower()
        if stream_input == "on":
            settings.stream_enabled = True
            print(f"{Fore.GREEN}Streaming enabled.")
        elif stream_input == "off":
            settings.stream_enabled = False
            print(f"{Fore.GREEN}Streaming disabled.")
        elif stream_input:
            print(f"{Fore.RED}Invalid value. Use on or off. Keeping {'on' if settings.stream_enabled else 'off'}.")

        return settings
