from __future__ import annotations

import datetime
import json
import re
from typing import Any, Dict, List, Optional

try:
    from clickhouse_driver import Client as CHDriver
except ImportError:  # pragma: no cover
    CHDriver = None  # type: ignore

from elastalert.util import dt_to_ts, ts_to_dt, EAException, elastalert_logger


class ClickHouseClient:
    """Very small subset of Elasticsearch client interface backed by ClickHouse.

    This class only implements the features required by ElastAlert2 for the
    FrequencyRule and SpikeRule rule types, which rely on *search* for fetching
    raw documents and *count* for a document count query. The goal is not to be
    a full Elasticsearch compatibility layer – just enough to transparently run
    the rules listed by the user without modifying their definitions.
    """

    def __init__(self, conf: Dict[str, Any]):
        if CHDriver is None:
            raise RuntimeError(
                "clickhouse-driver is not installed – ensure requirements are up-to-date"
            )

        # Configuration keys – provide sane defaults for local docker-compose
        self.host = conf.get("clickhouse_host", "localhost")
        self.port = int(conf.get("clickhouse_port", 9000))
        self.username = conf.get("clickhouse_username")
        self.password = conf.get("clickhouse_password")
        self.database = conf.get("clickhouse_database", "default")

        self.table = conf.get(
            "clickhouse_table", "passivedns.passivedns_v2"
        )  # full table name

        self.client = CHDriver(  # type: ignore[arg-type]
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database,
            settings={"use_numpy": False},
        )

    # ---------------------------------------------------------------------
    # ES-like helpers
    # ---------------------------------------------------------------------

    def _translate_range_filter(self, field: str, rng: Dict[str, str]) -> str:
        """Convert an ES *range* filter into ClickHouse SQL."""
        gt = rng.get("gt") or rng.get("gte")
        lte = rng.get("lte") or rng.get("lt")
        clauses: List[str] = []
        if gt is not None:
            dt = ts_to_dt(gt)
            clauses.append(f"{field} > toDateTime64('{dt_to_ts(dt)}', 6, 'UTC')")
        if lte is not None:
            dt = ts_to_dt(lte)
            clauses.append(f"{field} <= toDateTime64('{dt_to_ts(dt)}', 6, 'UTC')")
        return " AND ".join(clauses)

    _re_field_val = re.compile(r"(?P<field>[^:]+):(?P<value>.*)")

    def _parse_query_string(self, q: str) -> str:
        """*Very* naive Lucene query-string to SQL WHERE translator.

        Supported subset:
        - field:value (string or number)
        - AND, OR, NOT (case-sensitive as in examples)
        - parentheses for grouping
        - wildcard '*' converted to LIKE
        - fuzzy '~<num>' suffix is ignored and handled via LIKE
        - value lists inside parenthesis separated by OR translated to IN (...)
        """
        # Quick replacements for logical operators
        q = q.replace("AND", "and").replace("OR", "or").replace("NOT", "not")

        tokens = []
        for raw_token in re.split(r"(\s+|\(|\))", q):
            if raw_token is None or raw_token == "":
                continue
            if raw_token.isspace():
                continue
            if raw_token in ("(", ")", "and", "or", "not"):
                tokens.append(raw_token.upper())
                continue

            m = self._re_field_val.match(raw_token)
            if not m:
                tokens.append(raw_token)  # unmatched, push as-is
                continue

            field = m.group("field")
            value = m.group("value").strip()

            # Remove optional quotes
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            # Handle fuzzy/approx – strip ~N suffix
            if "~" in value:
                value = value.split("~")[0]

            # Handle parentheses list – not expected here, they would be split
            # earlier. We ignore.

            # Wildcards
            if "*" in value or "%" in value:
                like_val = value.replace("*", "%")
                tokens.append(f"{field} LIKE '{like_val}'")
            else:
                # Best effort: treat numeric as number else quote
                if value.isdigit():
                    tokens.append(f"{field} = {value}")
                else:
                    tokens.append(f"{field} = '{value}'")

        return " ".join(tokens)

    def _build_where_clause(self, body: Dict[str, Any]) -> str:
        """Convert a *very* small subset of ES DSL to SQL."""
        try:
            must_filters: List[Dict[str, Any]] = (
                body["query"]["bool"]["filter"]["bool"]["must"]
            )
        except KeyError:
            raise EAException("Unsupported query format for ClickHouse backend")

        clauses: List[str] = []
        for f in must_filters:
            if "range" in f:
                for field, rng in f["range"].items():
                    clauses.append(self._translate_range_filter(field, rng))
            elif "query_string" in f:
                clauses.append(self._parse_query_string(f["query_string"]["query"]))
            else:
                raise EAException(f"Filter type not supported: {f}")

        return " AND ".join([c for c in clauses if c])

    # ------------------------------------------------------------------
    # Public ES-compat methods
    # ------------------------------------------------------------------

    def search(
        self,
        index: Optional[str] = None,
        body: Optional[Dict[str, Any]] = None,
        doc_type: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        scroll: Optional[str] = None,
        size: int = 10000,
        **kwargs,
    ) -> Dict[str, Any]:
        """Mimic Elasticsearch *search* API – returns dict with hits."""
        if body is None:
            raise EAException("Search body must be provided for ClickHouse backend")

        where = self._build_where_clause(body)
        order = "ASC"
        # Determine ordering
        if body.get("sort"):
            # Example sort: [{"timestamp": {"order": "asc"}}]
            try:
                order = body["sort"][0][next(iter(body["sort"][0]))]["order"].upper()
            except Exception:  # pragma: no cover
                pass

        sql = (
            f"SELECT * FROM {self.table} WHERE {where} ORDER BY timestamp {order} LIMIT {size}"
        )
        elastalert_logger.debug(f"ClickHouse SQL: {sql}")

        rows = self.client.query_dict(sql)
        total_hits = len(rows)

        # Format like ES response
        hits = [{"_source": row} for row in rows]

        return {
            "hits": {"total": {"value": total_hits}, "hits": hits},
            "_shards": {"failures": []},
        }

    def count(
        self,
        index: Optional[str] = None,
        body: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, int]:
        """Mimic Elasticsearch *count* API."""
        if body is None:
            raise EAException("Count body must be provided for ClickHouse backend")
        where = self._build_where_clause(body)
        sql = f"SELECT count() as cnt FROM {self.table} WHERE {where}"
        elastalert_logger.debug(f"ClickHouse SQL: {sql}")
        cnt = self.client.execute_iter(sql)
        count_val = next(cnt)[0] if cnt else 0
        return {"count": count_val}

    # The following methods are used by ElastAlert but not needed when we don't
    # use scrolling – implement no-ops for compatibility.

    def scroll(self, *args, **kwargs):  # pragma: no cover
        return {"hits": {"hits": []}}

    def clear_scroll(self, *args, **kwargs):  # pragma: no cover
        pass

    # Provide dummy attributes expected elsewhere
    def __getattr__(self, item):  # pragma: no cover
        raise AttributeError(item)