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


def test_bucket_count_query():
    rule = {"table": "events", "timestamp_field": "ts"}
    start = datetime(2021, 1, 1, 0, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    from elastalert.datastores.sql_builders import build_bucket_count_query

    sql = build_bucket_count_query(rule, start, end, bucket_seconds=300)
    assert "GROUP BY bucket" in sql and "toStartOfInterval(" in sql


def test_spike_queries():
    rule = {"table": "e", "timestamp_field": "ts"}
    cur_start = datetime(2021, 1, 1, 1, 0, tzinfo=UTC)
    cur_end = datetime(2021, 1, 1, 2, 0, tzinfo=UTC)
    ref_start = cur_start - timedelta(hours=1)
    ref_end = cur_start

    from elastalert.datastores.sql_builders import build_spike_queries

    q = build_spike_queries(rule, cur_start, cur_end, ref_start, ref_end)
    assert "current" in q and "reference" in q
    assert "SELECT count()" in q["current"] and "SELECT count()" in q["reference"]