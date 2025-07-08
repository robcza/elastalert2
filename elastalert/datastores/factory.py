from __future__ import annotations

from typing import Any

from .elastic import ElasticSearchStore

# A lazy import is used for ClickHouse so we don't introduce an optional
# dependency until it is actually requested.


def get_store(conf: dict[str, Any]):
    """Return an appropriate *DataStore* implementation for the given config.

    The configuration dictionary **must** include a ``backend`` key once the
    ClickHouse support is fully implemented. Until then we default to
    ``'elasticsearch'`` to remain backwards-compatible with existing setups.
    """
    backend = conf.get("backend", "elasticsearch").lower()

    if backend == "elasticsearch":
        return ElasticSearchStore(conf)
    elif backend == "clickhouse":
        # The ClickHouse implementation will arrive in a subsequent task to
        # keep the initial abstraction focused and reviewable.
        from .clickhouse import ClickHouseStore  # pylint: disable=import-error

        return ClickHouseStore(conf)
    else:
        raise ValueError(f"Unsupported backend '{backend}'. Expected 'elasticsearch' or 'clickhouse'.")