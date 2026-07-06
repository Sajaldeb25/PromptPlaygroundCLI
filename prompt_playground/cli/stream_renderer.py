"""Terminal rendering for streaming and CoT-formatted responses."""

import sys
from collections.abc import Iterator

from colorama import Fore, Style

from prompt_playground.cli.cot_parser import CotParser, CotSection
from prompt_playground.services.chat_service import StreamResult


class StreamRenderer:
    """Print API output to the terminal with optional streaming and CoT styling."""

    def render_stream(
        self,
        deltas: Iterator[str],
        stream_result: StreamResult,
        cot_enabled: bool,
    ) -> tuple[str, int, str | None, bool]:
        """Consume a stream of text deltas and print to the terminal.

        Returns:
            (full_text, tokens, error, tags_found)
            tags_found is meaningful only when cot_enabled is True.
        """
        if stream_result.error:
            return "", 0, stream_result.error, False

        if cot_enabled:
            return self._render_stream_cot(deltas, stream_result)

        return self._render_stream_plain(deltas, stream_result)

    def render_blocking(
        self,
        text: str,
        cot_enabled: bool,
    ) -> tuple[str, bool]:
        """Print a complete response (non-streaming).

        Returns:
            (full_text, tags_found)
        """
        if not cot_enabled:
            print(f"{Fore.GREEN}AI: {text}")
            return text, False

        return self._render_blocking_cot(text)

    def _render_stream_plain(
        self,
        deltas: Iterator[str],
        stream_result: StreamResult,
    ) -> tuple[str, int, str | None, bool]:
        parts: list[str] = []
        print(f"{Fore.GREEN}AI: {Style.RESET_ALL}", end="")
        for delta in deltas:
            parts.append(delta)
            print(delta, end="", flush=True)
        print()
        return "".join(parts), stream_result.tokens, None, False

    def _render_stream_cot(
        self,
        deltas: Iterator[str],
        stream_result: StreamResult,
    ) -> tuple[str, int, str | None, bool]:
        parts: list[str] = []

        def write_fn(text: str, section: CotSection) -> None:
            if section == CotSection.THINKING:
                sys.stdout.write(f"{Fore.CYAN}{text}{Style.RESET_ALL}")
            elif section == CotSection.ANSWER:
                sys.stdout.write(f"{Fore.GREEN}{text}{Style.RESET_ALL}")
            else:
                sys.stdout.write(text)
            sys.stdout.flush()

        parser = CotParser(write_fn=write_fn)
        for delta in deltas:
            parts.append(delta)
            parser.feed(delta)
        parser.flush()
        print()

        parsed = parser.result()
        tags_found = parsed.has_tags
        if not tags_found and parsed.raw:
            print(f"{Fore.YELLOW}CoT tags not found in response{Style.RESET_ALL}")

        return parsed.raw or "".join(parts), stream_result.tokens, None, tags_found

    def _render_blocking_cot(self, text: str) -> tuple[str, bool]:
        parts: list[str] = []

        def write_fn(chunk: str, section: CotSection) -> None:
            parts.append(chunk)
            if section == CotSection.THINKING:
                print(f"{Fore.CYAN}{chunk}{Style.RESET_ALL}", end="")
            elif section == CotSection.ANSWER:
                print(f"{Fore.GREEN}{chunk}{Style.RESET_ALL}", end="")
            else:
                print(chunk, end="")

        parser = CotParser(write_fn=write_fn)
        parser.feed(text)
        parser.flush()
        print()

        parsed = parser.result()
        if not parsed.has_tags and text:
            print(f"{Fore.YELLOW}CoT tags not found in response{Style.RESET_ALL}")

        return parsed.raw or text, parsed.has_tags
