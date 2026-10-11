
import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import VALID_LEVELS, Event, build_event


def valid_data(**overrides):
    data = {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "source": "auth", "message": "Login ok"}
    data.update(overrides)
    return data


def test_valid_levels_contains_all_five():
    assert VALID_LEVELS == frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


def test_build_event_returns_event():
    event = build_event(valid_data(), filename="f.csv", line_number=1)
    assert isinstance(event, Event)
    assert event.level == "INFO"
    assert event.source == "auth"
    assert event.message == "Login ok"


def test_build_event_allows_empty_message():
    event = build_event(valid_data(message=""), filename="f.csv", line_number=1)
    assert event.message == ""


@pytest.mark.parametrize("field", ["timestamp", "level", "source"])
def test_build_event_rejects_empty_field(field):
    with pytest.raises(InvalidEventError) as exc_info:
        build_event(valid_data(**{field: "   "}), filename="f.csv", line_number=5)
    assert exc_info.value.field == field
    assert exc_info.value.line_number == 5


def test_build_event_rejects_bad_timestamp():
    with pytest.raises(InvalidTimestampError) as exc_info:
        build_event(valid_data(timestamp="not-a-date"), filename="f.csv", line_number=5,)
    assert exc_info.value.field == "timestamp"
    assert exc_info.value.line_number == 5
    assert exc_info.value.filename == "f.csv"


def test_build_event_rejects_naive_timestamp():
    with pytest.raises(InvalidTimestampError) as exc_info:
        build_event(valid_data(timestamp="2024-01-01T00:00:00"), filename="f.csv", line_number=4,)
    assert exc_info.value.field == "timestamp"


def test_build_event_rejects_unknown_level():
    with pytest.raises(InvalidEventError) as exc_info:
        build_event(valid_data(level="TRACE"), filename="f.csv", line_number=3)
    assert exc_info.value.field == "level"
    assert exc_info.value.line_number == 3