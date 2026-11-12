import requests

from youtube_tools.resolve import resolve_matches


def test_resolve_matches_uses_cache_and_searches_only_misses():
    calls = []

    def fake_search(query):
        calls.append(query)
        return {"title": f"t-{query}", "url": f"u-{query}"}

    cache = {"a": {"title": "cached", "url": "u-a"}}
    results, error = resolve_matches(["a", "b"], cache, fake_search)

    assert error is None
    assert calls == ["b"]
    assert results["a"]["title"] == "cached"
    assert results["b"]["url"] == "u-b"


def test_resolve_matches_stops_on_http_error_and_keeps_partial_results():
    def fake_search(query):
        if query == "b":
            raise requests.HTTPError("403 quotaExceeded")
        return {"title": query, "url": query}

    results, error = resolve_matches(["a", "b", "c"], {}, fake_search)

    assert "403" in error
    assert list(results) == ["a"]


def test_resolve_matches_records_none_when_no_match():
    results, error = resolve_matches(["a"], {}, lambda q: None)

    assert error is None
    assert results == {"a": None}
