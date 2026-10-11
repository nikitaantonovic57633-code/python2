import json
from pathlib import Path
from typing import Any

from .analysis import Aggregate
from .errors import ConfigError


def build_report(agg: Aggregate, top_n: int = 5, skipped: int = 0) -> dict[str, Any]:
    return {"total_events": agg.total,
            "by_level": dict(sorted(agg.by_level.items())),
            "by_source": dict(sorted(agg.by_source.items())),
            "top_error_sources": [{"source": source, "count": count} for source, count in agg.top_error_sources(top_n)],
            "first_timestamp": agg.first_timestamp.isoformat() if agg.first_timestamp else None,
            "last_timestamp": agg.last_timestamp.isoformat() if agg.last_timestamp else None,
            "skipped_lines": skipped}


def write_report(report: dict[str, Any], path: Path) -> None:
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise ConfigError(f"Не могу записать отчёт {path}: {exc}") from exc