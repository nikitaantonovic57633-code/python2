from dataclasses import dataclass
from datetime import datetime

from .errors import InvalidEventError, InvalidTimestampError

VALID_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
ERROR_LEVELS = frozenset({"ERROR", "CRITICAL"})


@dataclass(frozen=True)
class Event:
    timestamp: datetime
    level: str
    source: str
    message: str


def _get_str(data: dict, field: str, filename: str, line_number: int) -> str:
    if field not in data or data[field] is None:
        raise InvalidEventError(f"Пропущено обязательное поле {field}",
                                field=field,
                                line_number=line_number,
                                filename=filename)
    value = data[field]
    if not isinstance(value, str):
        raise InvalidEventError(f"Поле {field} должно быть строкой",
                                field=field,
                                line_number=line_number,
                                filename=filename)
    return value


def _require_str(data: dict, field: str, filename: str, line_number: int) -> str:
    value = _get_str(data, field, filename, line_number)
    if not value.strip():
        raise InvalidEventError(f"Поле {field} не должно быть пустым",
                                field=field,
                                line_number=line_number,
                                filename=filename)
    return value


def build_event(data: dict,
                *,
                filename: str,
                line_number: int) -> Event:
    if not isinstance(data, dict):
        raise InvalidEventError("Событие должно быть словарем",
                                line_number=line_number,
                                filename=filename)
    ts_raw = _require_str(data, "timestamp", filename=filename, line_number=line_number)
    if ts_raw.endswith("Z"):
        ts_raw = ts_raw[:-1] + "+00:00"
    try:
        ts = datetime.fromisoformat(ts_raw)
    except ValueError as exc:
        raise InvalidTimestampError(f"Неверный формат времени {ts_raw}",
                                    field="timestamp",
                                    line_number=line_number,
                                    filename=filename) from exc
    if ts.tzinfo is None:
        raise InvalidTimestampError(f"Временная метка без часового пояса: {ts_raw}",
            field="timestamp",
            line_number=line_number,
            filename=filename)
    level = _require_str(data, "level", filename=filename, line_number=line_number)
    if level not in VALID_LEVELS:
        raise InvalidEventError(f"Недопустимый уровень {level}",
                                field="level",
                                line_number=line_number,
                                filename=filename)
    source = _require_str(data, "source", filename=filename, line_number=line_number)
    message = _get_str(data, "message", filename=filename, line_number=line_number)

    return Event(timestamp=ts, level=level, source=source, message=message)