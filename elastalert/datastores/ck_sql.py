"""ClickHouse SQL builder helpers for ElastAlert 2.

This module centralises SQL template handling and translation of ElastAlert
``filter:`` DSL (currently limited to ``query_string`` clauses) into native
ClickHouse *WHERE* expressions.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

__all__ = [
    "SQLTemplates",
    "build_where_clause",
    "render_sql",
]


class SQLTemplates:
    """String constants for parametrised SQL blocks."""

    EVENT_SELECTION = (
        "SELECT *\n"
        "FROM {ck_database}.{ck_table}\n"
        "WHERE client_id = %(client_id)s\n"
        "  AND {additional_filters}\n"
        "  AND timestamp >= %(start)s\n"
        "  AND timestamp <  %(end)s\n"
        "ORDER BY timestamp"
    )

    COUNT_SELECTION = (
        "SELECT count() AS cnt\n"
        "FROM {ck_database}.{ck_table}\n"
        "WHERE client_id = %(client_id)s\n"
        "  AND timestamp BETWEEN %(start)s AND %(end)s\n"
        "  AND {additional_filters}"
    )


# ---------------------------------------------------------------------------
# Filter translation helpers
# ---------------------------------------------------------------------------

def _translate_query_string(expr: str) -> str:
    """Translate simple ``query_string`` expression into ClickHouse syntax.

    Supported flavour: ``key:value`` pairs — we do *not* attempt to parse the
    full Lucene grammar.
    """
    # Very naive split on first ':'
    if ':' not in expr:
        raise ValueError(f"Unsupported query_string expression: '{expr}'.")
    key, value = expr.split(':', 1)
    # Remove any surrounding quotes
    value = value.strip('"')
    return f"{key} = '{value}'"


def build_where_clause(filters: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    """Return SQL *WHERE* snippet generated from ElastAlert ``filter`` list.

    Only ``query_string`` filters are currently supported.  Unsupported filter
    types will raise ``ValueError`` so that calling code can fall back or abort.
    """
    parts: List[str] = []
    params: Dict[str, Any] = {}
    for flt in filters or []:
        if 'query_string' in flt:
            query_expr = flt['query_string']['query']
            if query_expr == "":
                # Skip empty strings per spec.
                continue
            parts.append(_translate_query_string(query_expr))
        else:
            raise ValueError(f"Unsupported filter type: {flt}")
    # Join with AND; ClickHouse treats empty WHERE as no filter.
    return (" AND ".join(parts), params)


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def render_sql(template: str, ctx: Dict[str, Any]) -> str:
    """Render *template* with *ctx* using :py:meth:`str.format`."""
    return template.format(**ctx)