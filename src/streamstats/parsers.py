import csv
import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Protocol

from .errors import InvalidEventError, UnsupportedFormatError

RawRow = tuple[dict[str, Any], int]
OnError = Callable[[InvalidEventError], None]


class Parser(Protocol):
    def __call__(self, path: Path, *, on_error: OnError) -> Iterator[RawRow]:
        ...


def iter_csv(path: Path, *, on_error: OnError) -> Iterator[RawRow]:
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return
            for row in reader:
                yield row, reader.line_num
    except OSError as exc:
        raise UnsupportedFormatError(f"Невозможно прочитать {path}: {exc}") from exc


def iter_jsonl(path: Path, *, on_error: OnError) -> Iterator[RawRow]:
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    on_error(InvalidEventError(f"Неверный JSON: {exc.msg}",
                                               line_number=line_number,
                                               filename=str(path)))
                    continue
                if not isinstance(data, dict):
                    on_error(InvalidEventError("Строка JSONL должна быть объектом",
                                               line_number=line_number,
                                               filename=str(path)))
                    continue
                yield data, line_number
    except OSError as exc:
        raise UnsupportedFormatError(f"Невозможно прочитать {path}: {exc}") from exc


PARSERS: dict[str, Parser] = {"csv": iter_csv, "jsonl": iter_jsonl}


def get_parser(fmt: str) -> Parser:
    parser = PARSERS.get(fmt)
    if parser is None:
        raise UnsupportedFormatError(f"Неподдерживаемый формат: {fmt}")
    return parser