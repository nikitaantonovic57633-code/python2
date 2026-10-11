import logging
from datetime import datetime, timezone

import pytest

from streamstats.analysis import Aggregate, EventStream
from streamstats.errors import InvalidEventError
from streamstats.models import Event


def make_event(level, source, second=0):
    return Event(timestamp=datetime(2024, 1, 1, 0, 0, second, tzinfo=timezone.utc),
                 level=level, source=source, message="m")


def test_aggregate_counts():
    agg = Aggregate()
    agg.add(make_event("INFO", "auth", 0))
    agg.add(make_event("ERROR", "db", 1))
    agg.add(make_event("CRITICAL", "db", 2))
    assert agg.total == 3
    assert agg.by_level["INFO"] == 1
    assert agg.by_source["db"] == 2
    assert agg.errors_by_source["db"] == 2
    assert agg.errors_by_source.get("auth", 0) == 0
    assert agg.first_timestamp == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert agg.last_timestamp == datetime(2024, 1, 1, 0, 0, 2, tzinfo=timezone.utc)


def test_aggregate_empty():
    agg = Aggregate()
    assert agg.total == 0
    assert agg.first_timestamp is None
    assert agg.last_timestamp is None
    assert agg.top_error_sources() == []


def test_top_error_sources_tie_break_deterministic():
    agg = Aggregate()
    for src in ("zeta", "alpha", "mike"):
        agg.add(make_event("ERROR", src))
    assert agg.top_error_sources() == [("alpha", 1), ("mike", 1), ("zeta", 1)]


def test_top_n_limit():
    agg = Aggregate()
    for i in range(10):
        for _ in range(i + 1):
            agg.add(make_event("ERROR", f"src{i:02d}"))
    top3 = agg.top_error_sources(3)
    assert [s for s, _ in top3] == ["src09", "src08", "src07"]


def test_event_stream_strict_mode_raises(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text("{broken}\n", encoding="utf-8")
    stream = EventStream([path], "jsonl", skip_invalid=False)
    with pytest.raises(InvalidEventError):
        list(stream)


def test_event_stream_skip_mode_continues(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text(
        '{"timestamp":"2024-01-01T00:00:00Z","level":"INFO","source":"a","message":"m"}\n'
        "{broken}\n"
        '{"timestamp":"2024-01-01T00:00:01Z","level":"ERROR","source":"b","message":"m"}\n', encoding="utf-8")
    stream = EventStream([path], "jsonl", skip_invalid=True)
    events = list(stream)
    assert len(events) == 2
    assert stream.skipped == 1


def test_event_stream_skip_mode_writes_warning(tmp_path, caplog):
    path = tmp_path / "bad.jsonl"
    path.write_text("{broken}\n", encoding="utf-8")
    stream = EventStream([path], "jsonl", skip_invalid=True)
    with caplog.at_level(logging.WARNING):
        list(stream)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"


def test_event_stream_aggregates_multiple_files(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    header = "timestamp,level,source,message\n"
    a.write_text(header + "2024-01-01T00:00:00Z,INFO,a,hi\n", encoding="utf-8")
    b.write_text(header + "2024-01-01T00:00:01Z,ERROR,b,boom\n", encoding="utf-8")
    stream = EventStream([a, b], "csv", skip_invalid=False)
    agg = Aggregate()
    for event in stream:
        agg.add(event)
    assert agg.total == 2
    assert agg.by_source == {"a": 1, "b": 1}