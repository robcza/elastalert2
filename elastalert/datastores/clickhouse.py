from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, Iterable, List, Mapping, Tuple

try:
    from clickhouse_driver import Client  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError(
        "clickhouse-driver is required for ClickHouse backend. Add it to your requirements.txt"
    ) from exc

from .base import BaseDataStore
from .ck_sql import build_where_clause, render_sql, SQLTemplates

__all__ = ["ClickHouseStore"]


class ClickHouseStore(BaseDataStore):
    """ClickHouse implementation of :class:`BaseDataStore`."""

    def __init__(self, config: Mapping[str, Any]):
        super().__init__(config)
        self._database: str = config.get("ck_database", "passivedns")
        self._table: str = config.get("ck_table", "passivedns_v2")
        self._client: Client = Client(
            host=config.get("ck_host", "localhost"),
            port=config.get("ck_port", 9000),
            user=config.get("ck_username", "default"),
            password=config.get("ck_password", ""),
            database=self._database,
            settings={"use_numpy": False},
        )
        # Column mapping constants
        self._ts_col = "timestamp"
        self._client_id_col = "client_id"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _to_python(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw ClickHouse *row* into dict compatible with ElastAlert."""
        doc = row.copy()
        # Alias to '@timestamp' for ElastAlert internal consumption
        ts_val = doc.get(self._ts_col)
        if ts_val is not None:
            # Ensure Python datetime with tzinfo UTC then isoformat
            if isinstance(ts_val, _dt.datetime):
                ts_iso = ts_val.replace(tzinfo=_dt.timezone.utc).isoformat()
            else:  # pragma: no cover – should not happen
                ts_iso = str(ts_val)
            doc["@timestamp"] = ts_iso
        return doc

    # ------------------------------------------------------------------
    # BaseDataStore interface
    # ------------------------------------------------------------------

    def search(self, **kwargs) -> List[Dict[str, Any]]:  # type: ignore[override]
        """Fetch full rows using the frequency-style template."""
        # Extract expected parameters similar to ES client
        rule_cfg = kwargs.pop("rule_config", {})  # Non-standard key we may pass
        params = self._build_param_dict(rule_cfg)
        # Custom timeframe override via kwargs
        if "start" in kwargs:
            params["start"] = kwargs.pop("start")
        if "end" in kwargs:
            params["end"] = kwargs.pop("end")
        additional_filters = self._build_additional_filters(rule_cfg)
        sql = render_sql(
            SQLTemplates.EVENT_SELECTION,
            {
                "ck_database": self._database,
                "ck_table": self._table,
                "additional_filters": additional_filters,
            },
        )
        rows, columns = self._client.execute(sql, params, with_column_types=True)
        col_names = [c[0] for c in columns]
        docs = [self._to_python(dict(zip(col_names, row))) for row in rows]
        return {
            "hits": {
                "hits": docs,
                "total": {"value": len(docs), "relation": "eq"},
            }
        }

    def count(self, **kwargs) -> int:  # type: ignore[override]
        rule_cfg = kwargs.pop("rule_config", {})
        params = self._build_param_dict(rule_cfg)
        if "start" in kwargs:
            params["start"] = kwargs.pop("start")
        if "end" in kwargs:
            params["end"] = kwargs.pop("end")
        additional_filters = self._build_additional_filters(rule_cfg)
        sql = render_sql(
            SQLTemplates.COUNT_SELECTION,
            {
                "ck_database": self._database,
                "ck_table": self._table,
                "additional_filters": additional_filters,
            },
        )
        res = self._client.execute(sql, params)
        count_val = int(res[0][0]) if res else 0
        return {"count": count_val}

    def iter_hits(self, **kwargs) -> Iterable[Dict[str, Any]]:  # type: ignore[override]
        # Use query with stream=True to avoid loading everything into memory
        rule_cfg = kwargs.pop("rule_config", {})
        params = self._build_param_dict(rule_cfg)
        additional_filters = self._build_additional_filters(rule_cfg)
        sql = render_sql(
            SQLTemplates.EVENT_SELECTION,
            {
                "ck_database": self._database,
                "ck_table": self._table,
                "additional_filters": additional_filters,
            },
        )
        with self._client.execute_iter(sql, params, with_column_types=True) as cursor:
            col_names = [c[0] for c in cursor.column_types]  # type: ignore[attr-defined]
            for row in cursor:
                yield self._to_python(dict(zip(col_names, row)))

    def close(self) -> None:  # type: ignore[override]
        try:
            self._client.disconnect()
        except Exception:  # pragma: no cover – disconnect best-effort
            pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_param_dict(self, rule_cfg: Mapping[str, Any]):
        now = _dt.datetime.utcnow()
        # Provide sane defaults if not overridden
        start = rule_cfg.get("start", now - _dt.timedelta(minutes=15))
        end = rule_cfg.get("end", now)
        return {
            "client_id": rule_cfg.get("client_id", ""),
            "start": start,
            "end": end,
        }

    def _build_additional_filters(self, rule_cfg: Mapping[str, Any]) -> str:
        filters = rule_cfg.get("filter", [])
        where_clause, _params = build_where_clause(filters)
        return where_clause or "1 = 1"  # no additional filters