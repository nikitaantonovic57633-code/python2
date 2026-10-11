import logging
from collections import Counter
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from .errors import InvalidEventError
from .models import ERROR_LEVELS, Event, build_event
from .parsers import get_parser

logger = logging.getLogger(__name__)


class EventStream:
    def __init__(self, paths: list[Path], fmt: str, skip_invalid: bool):
        self._paths = paths
        self._fmt = fmt
        self._skip_invalid = skip_invalid
        self.skipped = 0

    def _report(self, err: InvalidEventError) -> None:
        if self._skip_invalid:
            self.skipped += 1
            logger.warning("%s", err)
        else:
            raise err

    def __iter__(self) -> Iterator[Event]:
        parser = get_parser(self._fmt)
        for path in self._paths:
            for data, line_number in parser(path, on_error=self._report):
                try:
                    event = build_event(data, filename=str(path), line_number=line_number)
                except InvalidEventError as err:
                    self._report(err)
                    continue
                yield event


class Aggregate:
    def __init__(self):
        self.total = 0
        self.by_level: Counter[str] = Counter()
        self.by_source: Counter[str] = Counter()
        self.errors_by_source: Counter[str] = Counter()
        self.first_timestamp: datetime | None = None
        self.last_timestamp: datetime | None = None

    def add(self, event: Event) -> None:
        self.total += 1
        self.by_level[event.level] += 1
        self.by_source[event.source] += 1
        if event.level in ERROR_LEVELS:
            self.errors_by_source[event.source] += 1
        if self.first_timestamp is None or event.timestamp < self.first_timestamp:
            self.first_timestamp = event.timestamp
        if self.last_timestamp is None or event.timestamp > self.last_timestamp:
            self.last_timestamp = event.timestamp

    def top_error_sources(self, n: int = 5) -> list[tuple[str, int]]:
        return sorted(self.errors_by_source.items(), key=lambda kv: (-kv[1], kv[0]))[:n]