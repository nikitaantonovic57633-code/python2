import csv
import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from .errors import InvalidEventError, UnsupportedFormatError


RawRow = tuple[dict[str, Any], int]
OnError = Callable[[InvalidEventError], None]


def iter_csv(path: Path, *, on_error: OnError | None = None) -> Iterator[RawRow]:
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return
            for row in reader:
                yield row, reader.line_num
    except OSError as exc:
        raise UnsupportedFormatError(f"Невозможно прочитать {path}: {exc}") from exc


def iter_jsonl(path: Path, *, on_error: OnError | None = None) -> Iterator[RawRow]:
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    err = InvalidEventError(
                        f"Неверный JSON: {exc.msg}",
                        line_number=line_number,
                        filename=str(path),
                    )
                    if on_error is not None:
                        on_error(err)
                        continue
                    raise err from exc
                if not isinstance(data, dict):
                    err = InvalidEventError(
                        "Строка JSONL должна быть объектом",
                        line_number=line_number,
                        filename=str(path),
                    )
                    if on_error is not None:
                        on_error(err)
                        continue
                    raise err
                yield data, line_number
    except OSError as exc:
        raise UnsupportedFormatError(f"Невозможно прочитать {path}: {exc}") from exc


PARSERS = {"csv": iter_csv, "jsonl": iter_jsonl}


def get_parser(fmt: str):
    parser = PARSERS.get(fmt)
    if parser is None:
        raise UnsupportedFormatError(f"Неподдерживаемый формат: {fmt}")
    return parser