from __future__ import annotations


class StreamStatsError(Exception):
    """Базовое исключение пакета."""


class UnsupportedFormatError(StreamStatsError):
    """Неизвестный формат или нечитаемый файл."""


class ConfigError(StreamStatsError):
    """Некорректная конфигурация CLI."""


class InvalidEventError(StreamStatsError):
    """Строка не является валидным событием."""
    def __init__(self,
                 message: str,
                 *,
                 field: str | None = None,
                 line_number: int | None = None,
                 filename: str | None = None) -> None:
        parts = [message]
        if filename is not None and line_number is not None:
            parts.append(f"{filename}:{line_number}")
        super().__init__(" ".join(parts))
        self.field = field
        self.line_number = line_number
        self.filename = filename


class InvalidTimestampError(InvalidEventError):
    """Поле timestamp невалидно."""