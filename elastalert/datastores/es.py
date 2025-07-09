from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping

from elastalert.util import elasticsearch_client

from .base import BaseDataStore

__all__ = ["ElasticSearchStore"]


class ElasticSearchStore(BaseDataStore):
    """Thin wrapper around the native Elasticsearch Python client.

    This class exists purely to satisfy the :class:`BaseDataStore` contract and
    to keep the datastore factory symmetrical.  All heavy lifting is delegated
    to the real ES client already used by ElastAlert.
    """

    def __init__(self, config: Mapping[str, Any]):
        super().__init__(config)
        # Reuse helper that respects per-rule configuration
        self._client = elasticsearch_client(config)

    # ------------------------------------------------------------------
    # Delegated operations
    # ------------------------------------------------------------------

    def search(self, **kwargs) -> List[Dict[str, Any]]:  # type: ignore[override]
        response = self._client.search(**kwargs)
        return response["hits"]["hits"]

    def count(self, **kwargs) -> int:  # type: ignore[override]
        response = self._client.count(**kwargs)
        return int(response["count"])

    def iter_hits(self, **kwargs) -> Iterable[Dict[str, Any]]:  # type: ignore[override]
        # The existing util provides a generator `ESClient.scroll` which we can use
        # but to avoid pulling internals, implement a basic scroll-loop here.
        scroll = kwargs.pop("scroll", "5m")
        response = self._client.search(scroll=scroll, **kwargs)
        scroll_id = response.get("_scroll_id")
        hits = response["hits"]["hits"]
        for hit in hits:
            yield hit
        while hits:
            response = self._client.scroll(scroll_id=scroll_id, scroll=scroll)
            hits = response["hits"]["hits"]
            if not hits:
                break
            for hit in hits:
                yield hit

    def close(self) -> None:  # type: ignore[override]
        try:
            self._client.close()
        except Exception:  # pragma: no cover – not fatal
            pass