from __future__ import annotations

import abc
from typing import Any, Dict, Iterable, List, Mapping

__all__ = ["BaseDataStore"]


class BaseDataStore(abc.ABC):
    """Abstract contract for a datastore backend.

    The API is deliberately minimal and synchronous — ElastAlert processes data
    in blocking loops, so asynchronous drivers provide their own sync wrappers
    if desired.
    """

    #: Default timestamp field name to alias from the underlying storage engine.
    DEFAULT_TS_FIELD = "@timestamp"

    def __init__(self, config: Mapping[str, Any]):
        self._config: Mapping[str, Any] = config

    # ---------------------------------------------------------------------
    # Core query helpers
    # ---------------------------------------------------------------------

    @abc.abstractmethod
    def search(self, **kwargs) -> List[Dict[str, Any]]:
        """High-level data fetch returning *documents*.

        The concrete signature mirrors the Elasticsearch client subset used by
        ElastAlert.  Implementations MAY accept different keyword arguments but
        should *at least* provide sensible handling for ``index`` and ``body``.
        """

    @abc.abstractmethod
    def count(self, **kwargs) -> int:
        """Return an integer count for matching rows/events."""

    @abc.abstractmethod
    def iter_hits(self, **kwargs) -> Iterable[Dict[str, Any]]:
        """Yield rows lazily (streaming cursor)."""

    @abc.abstractmethod
    def close(self) -> None:
        """Gracefully release any pooled connections/resources."""