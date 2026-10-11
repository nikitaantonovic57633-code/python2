import pytest


@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("timestamp,level,source,message\n"
                    "2024-01-01T00:00:00Z,INFO,auth,Login ok\n"
                    "2024-01-01T00:00:01Z,ERROR,db,Timeout\n"
                    "2024-01-01T00:00:02Z,CRITICAL,db,Down\n"
                    "2024-01-01T00:00:03Z,INFO,auth,Logout\n",
                    encoding="utf-8")
    return path


@pytest.fixture
def sample_jsonl(tmp_path):
    path = tmp_path / "sample.jsonl"
    path.write_text('{"timestamp":"2024-01-01T00:00:00Z","level":"INFO","source":"auth","message":"Login ok"}\n'
                    '{"timestamp":"2024-01-01T00:00:01Z","level":"ERROR","source":"db","message":"Timeout"}\n'
                    '{"timestamp":"2024-01-01T00:00:02Z","level":"CRITICAL","source":"db","message":"Down"}\n'
                    '{"timestamp":"2024-01-01T00:00:03Z","level":"INFO","source":"auth","message":"Logout"}\n',
                    encoding="utf-8")
    return path