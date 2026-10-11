# streamstats

Анализатор логов CSV/JSONL. Читает файлы построчно, считает статистику, пишет JSON-отчёт.

## Установка

Нужен Python 3.10+

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -e ".[dev]"
```

`pytest` и `ruff` ставятся вместе с `.[dev]`.

## Запуск

```bash
python -m streamstats analyze INPUT [INPUT ...] --format csv|jsonl [--output REPORT.json] [--skip-invalid] [--top N]
```

- `--format csv|jsonl` — формат входных файлов, один для всех.
- `--output PATH` — путь к JSON-отчёту. По умолчанию `report.json`.
- `--skip-invalid` — пропускать невалидные строки вместо остановки.
- `--top N` — сколько источников ошибок показывать (по умолчанию 5).

Примеры:

```bash
# один файл
python -m streamstats analyze data.csv --format csv

# несколько файлов, свой output
python -m streamstats analyze a.jsonl b.jsonl --format jsonl --output report.json

# пропускать битые строки
python -m streamstats analyze data.jsonl --format jsonl --skip-invalid

# top-10 источников ошибок
python -m streamstats analyze data.csv --format csv --top 10
```

## Формат события

Обязательные поля:

- `timestamp` — ISO 8601, обязательно с таймзоной (`Z` или `+hh:mm`).
- `level` — одно из: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- `source` — непустая строка.
- `message` — строка, может быть пустой.

CSV с заголовком:

```csv
timestamp,level,source,message
2024-01-01T00:00:00Z,INFO,auth,Login ok
2024-01-01T00:00:01Z,ERROR,db,Timeout
```

JSONL — одна строка, один объект:

```jsonl
{"timestamp":"2024-01-01T00:00:00Z","level":"INFO","source":"auth","message":"Login ok"}
{"timestamp":"2024-01-01T00:00:01Z","level":"ERROR","source":"db","message":"Timeout"}
```

## Отчёт

```json
{"total_events": 3,
  "by_level": {"CRITICAL": 1, "ERROR": 1, "INFO": 1},
  "by_source": {"auth": 1, "db": 2},
  "top_error_sources": [{"source": "db", "count": 2}],
  "first_timestamp": "2024-01-01T00:00:00+00:00",
  "last_timestamp": "2024-01-01T00:00:02+00:00",
  "skipped_lines": 0}
```

### Пример с `--skip-invalid`

Вход `data.jsonl` — три строки, вторая битая:

```jsonl
{"timestamp":"2024-01-01T00:00:00Z","level":"INFO","source":"auth","message":"Login ok"}
{not valid json}
{"timestamp":"2024-01-01T00:00:02Z","level":"ERROR","source":"db","message":"Timeout"}
```

Запуск:

```bash
python -m streamstats analyze data.jsonl --format jsonl --skip-invalid
```

Отчёт:

```json
{"total_events": 2,
  "by_level": {"ERROR": 1, "INFO": 1},
  "by_source": {"auth": 1, "db": 1},
  "top_error_sources": [{"source": "db", "count": 1}],
  "first_timestamp": "2024-01-01T00:00:00+00:00",
  "last_timestamp": "2024-01-01T00:00:02+00:00",
  "skipped_lines": 1}
```

В `stderr` при этом появится:

```
WARNING: Неверный JSON: ... data.jsonl:2
```

Без `--skip-invalid` та же команда завершилась бы кодом 2 и отчёт не был бы создан.

## Обработка ошибок

По умолчанию CLI останавливается на первой невалидной строке, печатает `<файл>:<номер>` и завершается с кодом 2. С флагом `--skip-invalid` битые строки пропускаются, в лог идёт `WARNING`, а их число попадает в `skipped_lines` отчёта. Успешный запуск возвращает 0, ошибка — 2 (сюда же попадают ошибки `argparse` на неверных аргументах).

## Проверка

```bash
python -m pytest     # тесты
ruff check .         # линтер
```

`pytest` прогоняет тесты из `tests/`. `ruff` проверяет стиль и находит типичные ошибки — неиспользуемые импорты, неопределённые имена, длинные строки.