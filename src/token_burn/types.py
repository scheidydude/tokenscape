from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TokenUsage:
    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0

    @property
    def total(self) -> int:
        return self.input + self.output + self.cache_read + self.cache_write

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input=self.input + other.input,
            output=self.output + other.output,
            cache_read=self.cache_read + other.cache_read,
            cache_write=self.cache_write + other.cache_write,
        )


@dataclass
class Turn:
    message_id: str
    timestamp: datetime
    model: str
    usage: TokenUsage
    tools_used: list[str] = field(default_factory=list)
    bash_inputs: list[str] = field(default_factory=list)
    edited_files: list[str] = field(default_factory=list)
    user_text: str = ''
    cwd: str = ''
    project: str = ''


@dataclass
class Aggregate:
    usage: TokenUsage = field(default_factory=TokenUsage)
    turn_count: int = 0
