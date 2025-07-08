from datetime import datetime, timezone, timedelta

from elastalert.datastores.sql_builders import build_count_query, build_filter_predicates, build_time_predicate


UTC = timezone.utc


def test_time_predicate():
    start = datetime(2021, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2021, 1, 1, 1, 0, tzinfo=UTC)
    pred = build_time_predicate(start, end, 'ts')
    assert "ts >" in pred and "AND" in pred and "<=" in pred


def test_filter_predicate_term_and_query():
    filters = [
        {"term": {"service": "api"}},
        {"query_string": {"query": "error"}},
    ]
    clause = build_filter_predicates(filters)
    assert "service = 'api'" in clause
    assert "match(" in clause


def test_build_count_query_basic():
    rule = {
        "table": "logs",
        "timestamp_field": "ts",
        "filter": [{"term": {"level": "warn"}}],
    }
    start = datetime(2021, 1, 1, 0, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    sql = build_count_query(rule, start, end)
    assert "SELECT count()" in sql
    assert "FROM logs" in sql
    assert "level = 'warn'" in sql