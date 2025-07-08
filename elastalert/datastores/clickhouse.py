from __future__ import annotations

"""ClickHouse datastore implementation for ElastAlert 2.

This initial version offers **minimal** functionality—just enough to prove
round-trip connectivity and satisfy the Phase 02 test-cases. More advanced
features (SQL builders, spike detection, etc.) will follow in later phases.
"""

from typing import Any, Dict, List, Sequence, Tuple

from clickhouse_driver import Client  # type: ignore

from elastalert.util import ts_to_dt

from .sql_builders import build_count_query
from . import DataStore


class ClickHouseStore(DataStore):
    """A very thin wrapper around `clickhouse_driver.Client`."""

    def __init__(self, conf: dict[str, Any]):
        self._conf = conf
        self._client = self._create_client(conf)

    # ------------------------------------------------------------------
    # DataStore interface implementation
    # ------------------------------------------------------------------
    def search(self, sql: str, params: Sequence | None = None, **kwargs):  # noqa: D401
        """Execute a SQL query and return rows as list[dict]."""
        rows, columns = self._execute(sql, params, with_column_types=True)
        col_names = [name for name, _tp in columns]
        return [dict(zip(col_names, row)) for row in rows]

    def count(self, rule, start, end, **kwargs):  # noqa: D401
        # Simple count implementation assuming `rule['table']` and timestamp
        sql = build_count_query(rule, ts_to_dt(start), ts_to_dt(end))
        rows = self.search(sql)
        cnt = rows[0]["cnt"] if rows else 0
        return {end: cnt}

    def terms(self, *args, **kwargs):  # noqa: D401
        raise NotImplementedError("Terms aggregation not implemented for ClickHouse yet.")

    def aggregation(self, *args, **kwargs):  # noqa: D401
        raise NotImplementedError("Aggregation queries not implemented for ClickHouse yet.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _create_client(self, conf: dict[str, Any]) -> Client:
        return Client(
            host=conf.get("ck_host", "localhost"),
            port=conf.get("ck_port", 9000),
            database=conf.get("ck_database", "default"),
            user=conf.get("ck_user", "default"),
            password=conf.get("ck_password", ""),
            secure=conf.get("ck_secure", False),
            verify=conf.get("ck_verify", False),
        )

    def _execute(self, sql: str, params: Sequence | None = None, *, with_column_types=False):
        return self._client.execute(sql, params, with_column_types=with_column_types)

    # ------------------------------------------------------------------
    # Proxy other attributes to underlying client to ease migration
    # ------------------------------------------------------------------
    def __getattr__(self, item):
        return getattr(self._client, item)