import json
import subprocess
import sys


def run_cli(*args, cwd=None):
    return subprocess.run([sys.executable, "-m", "streamstats", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=cwd)


def write_csv(path, rows):
    header = "timestamp,level,source,message\n"
    lines = [",".join(r) for r in rows]
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_help_works():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "analyze" in result.stdout


def test_analyze_csv(tmp_path):
    src = tmp_path / "a.csv"
    write_csv(src,[("2024-01-01T00:00:00Z", "INFO", "auth", "Login"),
                   ("2024-01-01T00:00:01Z", "ERROR", "db", "Timeout"),
                   ("2024-01-01T00:00:02Z", "CRITICAL", "db", "Down")])
    out = tmp_path / "r.json"
    result = run_cli("analyze", str(src), "--format", "csv", "--output", str(out))
    assert result.returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_events"] == 3
    assert report["by_level"] == {"CRITICAL": 1, "ERROR": 1, "INFO": 1}
    assert report["top_error_sources"] == [{"source": "db", "count": 2}]
    assert report["skipped_lines"] == 0


def test_default_output(tmp_path):
    src = tmp_path / "a.csv"
    write_csv(src, [("2024-01-01T00:00:00Z", "INFO", "a", "m")])
    result = run_cli("analyze", str(src), "--format", "csv", cwd=str(tmp_path))
    assert result.returncode == 0
    assert (tmp_path / "report.json").exists()


def test_empty_file_produces_zero_report(tmp_path):
    src = tmp_path / "empty.csv"
    src.write_text("", encoding="utf-8")
    out = tmp_path / "r.json"
    result = run_cli("analyze", str(src), "--format", "csv", "--output", str(out))
    assert result.returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_events"] == 0
    assert report["first_timestamp"] is None
    assert report["last_timestamp"] is None


def test_strict_mode_reports_line_number(tmp_path):
    src = tmp_path / "bad.jsonl"
    valid = {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "source": "a", "message": "m"}
    write_jsonl(src, [valid] * 6)
    with src.open("a", encoding="utf-8") as f:
        f.write("{broken}\n")
    out = tmp_path / "r.json"
    result = run_cli("analyze", str(src), "--format", "jsonl", "--output", str(out))
    assert result.returncode == 2
    assert "7" in result.stderr
    assert not out.exists()


def test_skip_invalid_continues(tmp_path):
    src = tmp_path / "bad.jsonl"
    write_jsonl(src,[{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "source": "a", "message": "m"}])
    with src.open("a", encoding="utf-8") as f:
        f.write("{broken}\n")
    out = tmp_path / "r.json"
    result = run_cli("analyze", str(src), "--format", "jsonl", "--output", str(out), "--skip-invalid")
    assert result.returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["skipped_lines"] == 1


def test_csv_and_jsonl_reports_equal(tmp_path):
    rows = [("2024-01-01T00:00:00Z", "INFO", "auth", "Login"),
            ("2024-01-01T00:00:01Z", "ERROR", "db", "Timeout")]
    csv_path = tmp_path / "a.csv"
    jsonl_path = tmp_path / "a.jsonl"
    write_csv(csv_path, rows)
    write_jsonl(jsonl_path, [{"timestamp": t, "level": lvl, "source": src, "message": msg}
                             for (t, lvl, src, msg) in rows])
    out_csv = tmp_path / "csv.json"
    out_jsonl = tmp_path / "jsonl.json"
    run_cli("analyze", str(csv_path), "--format", "csv", "--output", str(out_csv))
    run_cli("analyze", str(jsonl_path), "--format", "jsonl", "--output", str(out_jsonl))
    assert json.loads(out_csv.read_text(encoding="utf-8")) == json.loads(out_jsonl.read_text(encoding="utf-8"))


def test_multiple_files_aggregated(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    write_csv(a, [("2024-01-01T00:00:00Z", "INFO", "auth", "hi")])
    write_csv(b, [("2024-01-01T00:00:01Z", "ERROR", "db", "boom")])
    out = tmp_path / "r.json"
    run_cli("analyze", str(a), str(b), "--format", "csv", "--output", str(out))
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_events"] == 2
    assert report["by_source"] == {"auth": 1, "db": 1}


def test_cyrillic_preserved(tmp_path):
    src = tmp_path / "ru.jsonl"
    write_jsonl(src,[{"timestamp": "2024-01-01T00:00:00Z",
                      "level": "INFO",
                      "source": "источник",
                      "message": "Привет"}])
    out = tmp_path / "r.json"
    run_cli("analyze", str(src), "--format", "jsonl", "--output", str(out))
    content = out.read_text(encoding="utf-8")
    assert "источник" in content
    assert "\\u" not in content  # ensure_ascii=False


def test_top_n_changes_output(tmp_path):
    src = tmp_path / "a.csv"
    rows = []
    for i in range(7):
        for _ in range(i + 1):
            rows.append(("2024-01-01T00:00:00Z", "ERROR", f"src{i:02d}", "m"))
    write_csv(src, rows)
    out = tmp_path / "r.json"
    run_cli("analyze", str(src), "--format", "csv", "--output", str(out), "--top", "3")
    report = json.loads(out.read_text(encoding="utf-8"))
    assert len(report["top_error_sources"]) == 3