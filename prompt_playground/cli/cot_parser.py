"""Parse and display Chain-of-Thought <thinking> / <answer> XML sections."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable


class CotSection(Enum):
    PLAIN = "plain"
    THINKING = "thinking"
    ANSWER = "answer"


class CotState(Enum):
    BEFORE_THINKING = auto()
    IN_THINKING = auto()
    BEFORE_ANSWER = auto()
    IN_ANSWER = auto()
    AFTER_ANSWER = auto()


@dataclass
class CotParseResult:
    raw: str = ""
    thinking: str | None = None
    answer: str | None = None
    has_tags: bool = False


WriteFn = Callable[[str, CotSection], None]


class CotParser:
    """Incremental parser for <thinking> and <answer> XML tags."""

    _OPEN_THINKING = "<thinking>"
    _CLOSE_THINKING = "</thinking>"
    _OPEN_ANSWER = "<answer>"
    _CLOSE_ANSWER = "</answer>"
    _WATCH_LEN = max(
        len(_OPEN_THINKING),
        len(_CLOSE_THINKING),
        len(_OPEN_ANSWER),
        len(_CLOSE_ANSWER),
    )

    def __init__(self, write_fn: WriteFn | None = None):
        self._write = write_fn or (lambda _text, _section: None)
        self._state = CotState.BEFORE_THINKING
        self._buffer = ""
        self._thinking_parts: list[str] = []
        self._answer_parts: list[str] = []
        self._plain_parts: list[str] = []
        self._thinking_header = False
        self._answer_header = False
        self._raw_parts: list[str] = []

    def feed(self, chunk: str) -> None:
        if not chunk:
            return
        self._raw_parts.append(chunk)
        self._buffer += chunk
        self._process_buffer()

    def flush(self) -> None:
        if self._buffer:
            self._emit_text(self._buffer, self._section_for_state())
            self._buffer = ""

    def result(self) -> CotParseResult:
        raw = "".join(self._raw_parts)
        thinking = "".join(self._thinking_parts).strip() or None
        answer = "".join(self._answer_parts).strip() or None
        has_tags = thinking is not None or answer is not None
        return CotParseResult(raw=raw, thinking=thinking, answer=answer, has_tags=has_tags)

    @classmethod
    def parse_static(cls, text: str) -> CotParseResult:
        parser = cls()
        parser.feed(text)
        parser.flush()
        return parser.result()

    def _section_for_state(self) -> CotSection:
        if self._state == CotState.IN_THINKING:
            return CotSection.THINKING
        if self._state == CotState.IN_ANSWER:
            return CotSection.ANSWER
        return CotSection.PLAIN

    def _process_buffer(self) -> None:
        while self._buffer:
            if self._state == CotState.BEFORE_THINKING:
                if not self._advance_past(self._OPEN_THINKING, CotState.IN_THINKING):
                    break
                self._show_thinking_header()
            elif self._state == CotState.IN_THINKING:
                if not self._emit_until(self._CLOSE_THINKING, CotSection.THINKING):
                    break
                self._state = CotState.BEFORE_ANSWER
            elif self._state == CotState.BEFORE_ANSWER:
                if not self._advance_past(self._OPEN_ANSWER, CotState.IN_ANSWER):
                    break
                self._show_answer_header()
            elif self._state == CotState.IN_ANSWER:
                if not self._emit_until(self._CLOSE_ANSWER, CotSection.ANSWER):
                    break
                self._state = CotState.AFTER_ANSWER
            else:
                self._emit_text(self._buffer, CotSection.PLAIN)
                self._buffer = ""
                break

    def _advance_past(self, tag: str, next_state: CotState) -> bool:
        idx = self._buffer.find(tag)
        if idx == -1:
            self._hold_back_unless_complete(tag)
            return False
        if idx > 0:
            self._emit_text(self._buffer[:idx], CotSection.PLAIN)
        self._buffer = self._buffer[idx + len(tag) :]
        self._state = next_state
        return True

    def _emit_until(self, close_tag: str, section: CotSection) -> bool:
        idx = self._buffer.find(close_tag)
        if idx == -1:
            self._hold_back_unless_complete(close_tag)
            if self._buffer:
                self._emit_text(self._buffer, section)
                self._buffer = ""
            return False
        if idx > 0:
            self._emit_text(self._buffer[:idx], section)
        self._buffer = self._buffer[idx + len(close_tag) :]
        return True

    def _hold_back_unless_complete(self, tag: str) -> None:
        """Keep a suffix that might be the start of an incomplete tag."""
        if len(self._buffer) < len(tag):
            return
        safe_len = len(self._buffer) - len(tag) + 1
        if safe_len <= 0:
            return
        safe = self._buffer[:safe_len]
        self._emit_text(safe, self._section_for_state())
        self._buffer = self._buffer[safe_len:]

    def _emit_text(self, text: str, section: CotSection) -> None:
        if not text:
            return
        if section == CotSection.THINKING:
            self._thinking_parts.append(text)
        elif section == CotSection.ANSWER:
            self._answer_parts.append(text)
        else:
            self._plain_parts.append(text)
        self._write(text, section)

    def _show_thinking_header(self) -> None:
        if not self._thinking_header:
            self._write("\nThinking:\n", CotSection.PLAIN)
            self._thinking_header = True

    def _show_answer_header(self) -> None:
        if not self._answer_header:
            self._write("\nAnswer:\n", CotSection.PLAIN)
            self._answer_header = True
