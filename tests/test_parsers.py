
from streamstats.parsers import iter_csv, iter_jsonl


def _ok(_):
    pass


def test_csv_reads_all_rows(sample_csv):
    rows = list(iter_csv(sample_csv, on_error=lambda e: None))
    assert len(rows) == 4
    assert rows[0][1] == 2
    assert rows[3][1] == 5


def test_jsonl_reads_all_rows(sample_jsonl):
    rows = list(iter_jsonl(sample_jsonl, on_error=lambda e: None))
    assert len(rows) == 4
    assert rows[0][1] == 1
    assert rows[3][1] == 4


def test_jsonl_broken_line_reports_number(tmp_path):
    path = tmp_path / "broken.jsonl"
    path.write_text("\n".join(['{"timestamp":"2024-01-01T00:00:00Z","level":"INFO","source":"a","message":"ok"}']
                              + ['{"timestamp":"2024-01-01T00:00:00Z","level":"INFO","source":"a","message":"ok"}'] * 5
                              + ["{not json}"]) + "\n", encoding="utf-8")
    errors = []
    list(iter_jsonl(path, on_error=errors.append))
    assert len(errors) == 1
    assert errors[0].line_number == 7
    assert errors[0].filename == str(path)


def test_csv_and_jsonl_produce_same_rows(sample_csv, sample_jsonl):
    csv_rows = [row for row, _ in iter_csv(sample_csv, on_error=lambda e: None)]
    jsonl_rows = [row for row, _ in iter_jsonl(sample_jsonl, on_error=lambda e: None)]
    assert csv_rows == jsonl_rows


def test_jsonl_preserves_cyrillic(tmp_path):
    path = tmp_path / "ru.jsonl"
    path.write_text(
        '{"timestamp":"2024-01-01T00:00:00Z","level":"INFO","source":"источник","message":"Привет, мир"}\n',
        encoding="utf-8")
    rows = list(iter_jsonl(path, on_error=lambda e: None))
    data, _ = rows[0]
    assert data["source"] == "источник"
    assert data["message"] == "Привет, мир"


def test_source_files_not_modified(sample_csv, sample_jsonl):
    csv_before = sample_csv.read_bytes()
    jsonl_before = sample_jsonl.read_bytes()
    list(iter_csv(sample_csv, on_error=_ok))
    list(iter_jsonl(sample_jsonl, on_error=_ok))
    assert sample_csv.read_bytes() == csv_before
    assert sample_jsonl.read_bytes() == jsonl_before


def test_parser_is_streaming(tmp_path):
    import tracemalloc
    path = tmp_path / "large.csv"
    n = 100_000
    with path.open("w", encoding="utf-8") as f:
        f.write("timestamp,level,source,message\n")
        for _ in range(n):
            f.write("2024-01-01T00:00:00Z,INFO,src,msg\n")
    tracemalloc.start()
    count = sum(1 for _ in iter_csv(path, on_error=_ok))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert count == n
    assert peak < 2_000_000, f"пиковая память {peak:,} байт — файл читается целиком?"