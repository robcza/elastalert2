"""Utility helpers to translate ElastAlert rule filters into ClickHouse SQL.

This minimal set is enough to power *frequency* and *spike* detection rules for
straight-forward use-cases. The API is intentionally *internal* – callers should
use the high-level helpers such as :pyfunc:`build_frequency_query`.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, List

__all__ = [
    "build_time_predicate",
    "build_filter_predicates",
    "build_frequency_query",
    "build_count_query",
    "build_bucket_count_query",
    "build_spike_queries",
]

ISO_FMT = "%Y-%m-%d %H:%M:%S"


def _ts(dt: _dt.datetime) -> str:
    """Render *UTC* datetime to ClickHouse `DateTime` literal."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return dt.astimezone(_dt.timezone.utc).strftime(ISO_FMT)


# ---------------------------------------------------------------------------
# Predicate builders
# ---------------------------------------------------------------------------

def build_time_predicate(start: _dt.datetime, end: _dt.datetime, field: str) -> str:
    """`{field} > start AND {field} <= end`"""
    return f"{field} > toDateTime('{_ts(start)}') AND {field} <= toDateTime('{_ts(end)}')"


def build_filter_predicates(filters: List[dict[str, Any]]) -> str:
    """Translate *very* small subset of ES filter DSL into SQL.

    Supported:
    1. term: {"term": {"field": "value"}}
    2. query_string with simple `query: 'foo AND bar'` (passed verbatim into ClickHouse `match`)
    """
    clauses: list[str] = []
    for f in filters or []:
        if "term" in f:
            for field, value in f["term"].items():
                clauses.append(f"{field} = '{value}'")
        elif "query_string" in f:
            q = f["query_string"]["query"].replace("\"", "")
            clauses.append(f"match(all, '{q}')")  # assumes `all` index
    return " AND ".join(clauses)


# ---------------------------------------------------------------------------
# High-level query helpers
# ---------------------------------------------------------------------------

def build_count_query(rule: dict[str, Any], start: _dt.datetime, end: _dt.datetime) -> str:
    table = rule.get("table") or rule.get("ck_table", "logs")
    ts_field = rule.get("timestamp_field", "@timestamp")
    where = [build_time_predicate(start, end, ts_field)]
    extra = build_filter_predicates(rule.get("filter", []))
    if extra:
        where.append(extra)
    where_clause = " AND ".join(where)
    return f"SELECT count() AS cnt FROM {table} WHERE {where_clause}"


def build_frequency_query(rule: dict[str, Any], start: _dt.datetime, end: _dt.datetime) -> str:
    """Return SQL that yields one row per event (no grouping). For frequency
    rules we only need *count* so this delegates to build_count_query."""
    return build_count_query(rule, start, end)


# ---------------------------------------------------------------------------
# Aggregated counts / buckets
# ---------------------------------------------------------------------------


def build_bucket_count_query(rule: dict[str, Any], start: _dt.datetime, end: _dt.datetime, bucket_seconds: int) -> str:
    """Return SQL that counts rows grouped into fixed-size time buckets."""
    table = rule.get("table") or rule.get("ck_table", "logs")
    ts_field = rule.get("timestamp_field", "@timestamp")
    where = [build_time_predicate(start, end, ts_field)]
    extra = build_filter_predicates(rule.get("filter", []))
    if extra:
        where.append(extra)
    where_clause = " AND ".join(where)
    bucket_expr = f"toStartOfInterval({ts_field}, INTERVAL {bucket_seconds} SECOND) AS bucket"
    return (
        f"SELECT {bucket_expr}, count() AS cnt FROM {table} "
        f"WHERE {where_clause} GROUP BY bucket ORDER BY bucket"
    )


# ---------------------------------------------------------------------------
# Spike detection helpers
# ---------------------------------------------------------------------------


def build_spike_queries(rule: dict[str, Any], cur_start: _dt.datetime, cur_end: _dt.datetime,
                        ref_start: _dt.datetime, ref_end: _dt.datetime) -> dict[str, str]:
    """Return two count queries for current and reference windows."""
    return {
        "current": build_count_query(rule, cur_start, cur_end),
        "reference": build_count_query(rule, ref_start, ref_end),
    }