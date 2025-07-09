Datastore Abstraction Layer
============================

ElastAlert 2 historically interacted **only** with Elasticsearch / OpenSearch.
From version 2.TBD.TBD a pluggable *datastore* layer allows additional storage
engines to be added without modifying rule YAML or the core alert engine.

Design goals
------------

* **Back-compatibility** – existing rules continue to work unchanged.
* **Minimal surface area** – the abstraction exposes only a handful of methods
  used by rule processing (`search`, `count`, `iter_hits`, `close`).
* **Lazy loading** – optional dependencies (e.g. `clickhouse-driver`) are
  imported only when the backend is requested.
* **Extensibility** – new back-ends implement `BaseDataStore` and register via
  the factory in `elastalert.datastores`.

Module layout
-------------

``elastalert/datastores/`` contains the implementation:  ::

    base.py          # BaseDataStore ABC
    es.py            # ElasticSearchStore (existing logic wrapped)
    clickhouse.py    # ClickHouseStore (native driver + SQL builders)
    ck_sql.py        # Helper functions for generating ClickHouse SQL
    __init__.py      # get_datastore() factory

Choosing a backend
------------------

A rule (or global ``config.yaml``) selects the backend via the ``backend`` key.
If omitted the default is ``elasticsearch``.

.. code-block:: yaml

    backend: clickhouse
    ck_host: clickhouse
    ck_database: passivedns

The alert engine instantiates the appropriate store lazily when the rule
executes.

Adding your own backend
-----------------------

1. Create a new module under ``elastalert/datastores/`` implementing
   ``BaseDataStore``.
2. Add an import branch in `elastalert/datastores/__init__.py::_load_store`.
3. Write unit tests to achieve ≥90 % coverage.

That’s it!  The rest of ElastAlert 2 remains unchanged.