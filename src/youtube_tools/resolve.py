from typing import Callable

import requests


def resolve_matches(
    queries: list[str],
    cache: dict[str, dict[str, str | None]],
    search: Callable[[str], dict[str, str | None] | None],
) -> tuple[dict[str, dict[str, str | None] | None], str | None]:
    """Resolve each query to {"title", "url"}, reusing `cache` and calling `search` only on misses.

    A query with no YouTube match maps to None. If `search` raises an HTTP error (e.g. quota
    exceeded), resolution stops and the results so far are returned with the error message, so
    nothing already paid for is lost. Returns (results, error_or_None); unresolved queries are
    absent from results.
    """
    results: dict[str, dict[str, str | None] | None] = {}
    for query in queries:
        if query in cache:
            results[query] = cache[query]
            continue
        try:
            results[query] = search(query)
        except requests.HTTPError as exc:
            return results, str(exc)
    return results, None
