from __future__ import annotations

from typing import Any

from . import DataStore


class ClickHouseStore(DataStore):
    """Placeholder implementation for ClickHouse support.

    The concrete implementation will be developed in *02_clickhouse_driver.md*.
    For now the class exists so the factory can import it without raising an
    ImportError when someone experiments with the *clickhouse* backend.
    """

    def __init__(self, conf: dict[str, Any]):  # noqa: D401
        self._conf = conf
        raise NotImplementedError(
            "ClickHouse backend is not implemented yet. Follow the roadmap in 'tasks/02_clickhouse_driver.md'."
        )

    # -------------------------------
    # DataStore required interface
    # -------------------------------
    def search(self, *args, **kwargs):
        raise NotImplementedError

    def count(self, *args, **kwargs):
        raise NotImplementedError

    def terms(self, *args, **kwargs):
        raise NotImplementedError

    def aggregation(self, *args, **kwargs):
        raise NotImplementedError