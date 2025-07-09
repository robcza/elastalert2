from __future__ import annotations

"""Datastore abstraction layer.

This package provides a thin factory that creates a concrete implementation of
:class:`BaseDataStore` depending on the ``backend`` string configured either at
rule-level or in the global configuration.  Today two back-ends are supported:

* ``elasticsearch`` – the historical default. Handled via
  :class:`ElasticSearchStore` which simply delegates to the existing helper
  functions and native Elasticsearch client.
* ``clickhouse``   – new in ElastAlert 2.  Backed by :class:`ClickHouseStore`.

The concrete stores are lazily imported to keep optional dependencies light –
for example :pypi:`clickhouse-driver` is only required when ClickHouse support
is requested.

The public API intentionally mirrors the subset of Elasticsearch Python client
methods required by ElastAlert core (``search``, ``count``, ``iter_hits`` and
``close``).  This allows the core engine to remain unchanged while we migrate
internally towards a proper datastore-agnostic flow.
"""

from typing import Any, Mapping

# NOTE: explicit re-export for type checkers
__all__ = [
    "BaseDataStore",
    "ElasticSearchStore",
    "ClickHouseStore",
    "get_datastore",
]


try:
    from .base import BaseDataStore  # noqa: F401
except Exception as exc:  # pragma: no cover – should never happen
    raise


def _load_store(name: str):
    """Import helper keeping optional deps isolated."""
    if name == "elasticsearch":
        from .es import ElasticSearchStore  # noqa: WPS442 (import inside fn)

        return ElasticSearchStore
    elif name == "clickhouse":
        from .clickhouse import ClickHouseStore  # noqa: WPS442

        return ClickHouseStore
    else:
        raise ValueError(f"Unsupported backend '{name}'.")


def get_datastore(config: Mapping[str, Any]):
    """Return datastore instance given a *config* mapping.

    The mapping is expected to expose a ``backend`` key – either at rule-level
    or top-level settings.  Missing key defaults to *elasticsearch* for full
    backward compatibility.
    """
    backend = (config.get("backend") or config.get("es_client") or "elasticsearch").lower()
    store_cls = _load_store(backend)
    return store_cls(config)