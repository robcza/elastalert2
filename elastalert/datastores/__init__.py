from abc import ABC, abstractmethod


class DataStore(ABC):
    """Abstract base class defining the required interface for a backend datastore.

    Concrete implementations (e.g. ElasticSearchStore, ClickHouseStore) must provide
    methods that ElastAlert uses to query data. The method signatures purposefully
    mirror the Elasticsearch client so that existing call-sites need minimal
    adjustments while we transition to a pluggable backend model.
    """

    @abstractmethod
    def search(self, *args, **kwargs):  # noqa: D401
        """Run a search query and return raw results."""
        raise NotImplementedError

    @abstractmethod
    def count(self, *args, **kwargs):  # noqa: D401
        """Return a document count for a query."""
        raise NotImplementedError

    @abstractmethod
    def terms(self, *args, **kwargs):  # noqa: D401
        """Return terms aggregation buckets for a query."""
        raise NotImplementedError

    @abstractmethod
    def aggregation(self, *args, **kwargs):  # noqa: D401
        """Run a generic aggregation query and return buckets/results."""
        raise NotImplementedError

    # Convenience helpers -----------------------------------------------------
    # The original ElastAlert code relies on scroll/clear_scroll for large
    # result sets. These are kept outside the ABC contract for now because
    # not every backend will support the same mechanics. Implementations that
    # *do* support them (e.g. Elasticsearch) should expose compatible methods
    # so existing call-sites keep working during the migration period.

    def scroll(self, *args, **kwargs):  # type: ignore[override]
        raise NotImplementedError

    def clear_scroll(self, *args, **kwargs):  # type: ignore[override]
        raise NotImplementedError