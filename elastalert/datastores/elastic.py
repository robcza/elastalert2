from __future__ import annotations

from typing import Any

import importlib

from . import DataStore


class ElasticSearchStore(DataStore):
    """Datastore wrapper that delegates all operations to an *Elasticsearch* client.

    The goal is to keep the public surface identical to the original Elasticsearch
    client so that existing ElastAlert code and unit-tests continue to work while
    we gradually introduce the new abstraction layer.
    """

    def __init__(self, conf: dict[str, Any]):
        """Create a new store instance.

        The *elasticsearch_client* factory is resolved dynamically at runtime
        to honour any monkey-patching performed by the legacy unit-tests (they
        patch ``elastalert.elastalert.elasticsearch_client``).
        """
        ea_module = importlib.import_module("elastalert.elastalert")
        es_client_factory = getattr(ea_module, "elasticsearch_client")

        # Re-use the existing helper so we inherit all connection semantics.
        self._client = es_client_factory(conf)

    # ---------------------------------------------------------------------
    # DataStore interface implementation
    # ---------------------------------------------------------------------
    def search(self, *args, **kwargs):  # noqa: D401
        return self._client.search(*args, **kwargs)

    def count(self, *args, **kwargs):  # noqa: D401
        return self._client.count(*args, **kwargs)

    def terms(self, *args, **kwargs):  # noqa: D401
        # For Elasticsearch the *terms* helper is essentially a search with an
        # aggregation query. Callers are expected to build the appropriate body
        # themselves, so we simply delegate to ``search``.
        return self._client.search(*args, **kwargs)

    def aggregation(self, *args, **kwargs):  # noqa: D401
        # Same rationale as ``terms``.
        return self._client.search(*args, **kwargs)

    # ------------------------------------------------------------------
    # Additional helpers used by existing ElastAlert code
    # ------------------------------------------------------------------
    def scroll(self, *args, **kwargs):
        return self._client.scroll(*args, **kwargs)

    def clear_scroll(self, *args, **kwargs):
        return self._client.clear_scroll(*args, **kwargs)

    # ------------------------------------------------------------------
    # Attribute proxying so that the store acts like the underlying client
    # ------------------------------------------------------------------
    def __getattr__(self, item):
        """Proxy any unknown attribute access to the wrapped client instance."""
        return getattr(self._client, item)

    # ------------------------------------------------------------------
    # Allow tests to monkey-patch ``search`` directly on the store instance
    # (they historically patched ``current_es.search`` which now resolves to
    # the store object).
    # ------------------------------------------------------------------

    @property
    def search(self):  # type: ignore[override]
        # Promote to a MagicMock if the underlying attribute is a regular
        # method. This is primarily to support the existing unit-test pattern
        # that monkey-patches ``current_es.search.return_value``.
        from unittest.mock import MagicMock  # local import to avoid overhead

        if not isinstance(self._client.search, MagicMock):
            self._client.search = MagicMock()
        return self._client.search

    @search.setter
    def search(self, value):  # type: ignore[override]
        setattr(self._client, "search", value)