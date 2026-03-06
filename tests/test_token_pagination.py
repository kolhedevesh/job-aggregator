import json
from types import SimpleNamespace

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

    @property
    def text(self):
        try:
            return json.dumps(self._data)
        except Exception:
            return str(self._data)


def test_token_pagination_fetches_different_pages(monkeypatch):
    # simulate two-page provider: first call (no token) returns A + token, second call with token returns B
    def fake_get(url, params, timeout):
        q = params.get("q")
        token = params.get("next_page_token")
        if not token:
            data = {"jobs_results": [{"id": "A1", "title": "Alpha"}], "next_page_token": "tok1"}
            return DummyResp(data, status=200)
        if token == "tok1":
            data = {"jobs_results": [{"id": "B1", "title": "Beta"}], "next_page_token": None}
            return DummyResp(data, status=200)
        return DummyResp({}, status=400)

    monkeypatch.setattr(sc.requests, "get", fake_get)
    client = sc.SerpApiClient(api_key="k")
    res1, meta1 = client.search_page(query="engineer", next_page_token=None, num=10)
    assert meta1.get("next_page_token") == "tok1"
    res2, meta2 = client.search_page(query="engineer", next_page_token="tok1", num=10)
    assert res1 != res2
    assert len(res1) == 1 and res1[0]["id"] == "A1"
    assert len(res2) == 1 and res2[0]["id"] == "B1"
