import argparse
import logging
import sys
from pathlib import Path

from .analysis import Aggregate, EventStream
from .errors import ConfigError, StreamStatsError
from .report import build_report, write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="streamstats",
                                     description="Потоковый анализатор событий CSV/JSONL")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Проанализировать входные файлы")
    analyze.add_argument("inputs", nargs="+", type=Path, help="Входные файлы")
    analyze.add_argument(
        "--format", choices=("csv", "jsonl"), required=True, help="Формат входных файлов")
    analyze.add_argument("--output",
                         type=Path,
                         default=Path("report.json"),
                         help="Путь к JSON-отчёту (по умолчанию report.json)")
    analyze.add_argument("--skip-invalid",
                         action="store_true",
                         help="Пропускать невалидные строки вместо остановки")
    analyze.add_argument("--top",
                         type=int,
                         default=5,
                         help="Сколько источников ошибок показывать (по умолчанию 5)")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s", stream=sys.stderr)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.top < 1:
            raise ConfigError("--top должен быть >= 1")
        for path in args.inputs:
            if not path.exists():
                raise ConfigError(f"Файл не найден: {path}")
        agg = Aggregate()
        stream = EventStream(args.inputs, args.format, args.skip_invalid)
        for event in stream:
            agg.add(event)
        report = build_report(agg, top_n=args.top, skipped=stream.skipped)
        write_report(report, args.output)
        return 0
    except ConfigError as err:
        print(f"Ошибка конфигурации: {err}", file=sys.stderr)
        return 2
    except StreamStatsError as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())