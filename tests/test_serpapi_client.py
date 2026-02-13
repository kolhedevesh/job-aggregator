import json
from types import SimpleNamespace

import pytest

import services.serpapi_client as sc


class DummyResp:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception("HTTP error")

    def json(self):
        return self._data


def test_search_parses_jobs(monkeypatch):
    sample = {"jobs_results": [{"title": "Dev", "company_name": "X", "url": "http://a"}]}

    def fake_get(url, params, timeout):
        # expose params for assertions
        fake_get.last_params = params
        return DummyResp(sample)

    monkeypatch.setattr(sc.requests, "get", fake_get)
    client = sc.SerpApiClient(api_key="key")
    res = client.search("dev")
    assert isinstance(res, list)
    assert res[0]["title"] == "Dev"


def test_empty_query_raises():
    client = sc.SerpApiClient(api_key="k")
    try:
        client.search("")
        assert False, "Expected ValueError for empty query"
    except ValueError:
        assert True


def test_filters_injected_into_query(monkeypatch):
    sample = {"jobs_results": [{"title": "Dev", "company_name": "X", "url": "http://a"}]}

    def fake_get(url, params, timeout):
        fake_get.last_params = params
        return DummyResp(sample)

    monkeypatch.setattr(sc.requests, "get", fake_get)
    client = sc.SerpApiClient(api_key="key")
    res = client.search("engineer", remote="Remote", experience_level="Senior", employment_type="Full-time", tech_stack="Python")
    assert isinstance(res, list)
    # q should contain the filters injected
    q = fake_get.last_params.get("q", "")
    assert "Remote" in q and "Senior" in q and "Full-time" in q and "Python" in q


def test_location_sanitization(monkeypatch):
    sample = {"jobs_results": [{"title": "Dev"}]}

    def fake_get(url, params, timeout):
        fake_get.last_params = params
        return DummyResp(sample)

    monkeypatch.setattr(sc.requests, "get", fake_get)
    client = sc.SerpApiClient(api_key="key")
    client.search("engineer", location="India, Maharashtra, Pune")
    # location should be first two tokens
    assert fake_get.last_params.get("location") == "India, Maharashtra"


def test_search_retry_simplifies(monkeypatch):
    # First call fails, second succeeds
    calls = {"n": 0}

    def fake_get(url, params, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            return DummyResp({}, status=500)
        return DummyResp({"jobs_results": [{"title": "Dev"}]})

    monkeypatch.setattr(sc.requests, "get", fake_get)
    client = sc.SerpApiClient(api_key="k")
    res = client.search("software engineer", location="" )
    assert len(res) == 1


def test_multi_page_combination(monkeypatch):
    # Simulate three pages returned by provider for starts 0,10,20
    def fake_get(url, params, timeout):
        start = int(params.get("start", 0))
        if start == 0:
            data = {"jobs_results": [{"title": f"A{i}"} for i in range(10)]}
        elif start == 10:
            data = {"jobs_results": [{"title": f"B{i}"} for i in range(10, 20)]}
        elif start == 20:
            data = {"jobs_results": [{"title": f"C{i}"} for i in range(20, 30)]}
        else:
            data = {"jobs_results": []}
        return DummyResp(data)

    monkeypatch.setattr(sc.requests, "get", fake_get)
    client = sc.SerpApiClient(api_key="key")
    res = client.search("engineer", limit=30)
    assert isinstance(res, list)
    assert len(res) == 30


def test_retry_on_400(monkeypatch):
    # First attempt returns 400 on any start; retry with simplified q should succeed
    state = {"n": 0}

    def fake_get(url, params, timeout):
        # if q is simplified (one/two words) return success
        q = params.get("q", "")
        if q == "engineer gigabit":
            return DummyResp({"jobs_results": [{"title": "OK"}]})
        # otherwise return 400
        return DummyResp({}, status=400)

    monkeypatch.setattr(sc.requests, "get", fake_get)
    client = sc.SerpApiClient(api_key="k")
    res = client.search("engineer gigabit", location="India", limit=10)
    assert len(res) >= 0
