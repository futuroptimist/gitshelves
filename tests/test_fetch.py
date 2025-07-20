from datetime import datetime
import types

import gitshelves.fetch as fetch


def test_fetch_single_page(monkeypatch):
    called = {}

    def fake_get(url, headers=None, params=None, timeout=10):
        called['headers'] = headers
        called['params'] = params.copy()

        class Resp:
            links = {}

            @staticmethod
            def raise_for_status():
                pass

            @staticmethod
            def json():
                return {'items': [{'id': 1}]}

        return Resp()

    monkeypatch.setattr(fetch.requests, 'get', fake_get)
    items = fetch.fetch_user_contributions('me', start_year=2022, end_year=2022)

    assert items == [{'id': 1}]
    assert called['headers'] == {}
    assert called['params']['page'] == 1
    assert '2022-01-01' in called['params']['q']
    assert '2022-12-31' in called['params']['q']


def test_fetch_multiple_pages_with_token(monkeypatch):
    pages = []
    headers_used = []
    queries = []

    def fake_get(url, headers=None, params=None, timeout=10):
        pages.append(params['page'])
        headers_used.append(headers)
        queries.append(params['q'])

        class Resp:
            def __init__(self, page):
                self.links = {'next': 'x'} if page == 1 else {}
                self.page = page

            @staticmethod
            def raise_for_status():
                pass

            def json(self):
                return {'items': [{'page': self.page}]}

        return Resp(params['page'])

    class DummyDateTime(datetime):
        @classmethod
        def utcnow(cls):
            return datetime(2021, 1, 1)

    monkeypatch.setattr(fetch, 'datetime', DummyDateTime)
    monkeypatch.setattr(fetch.requests, 'get', fake_get)

    items = fetch.fetch_user_contributions('me', token='T')

    assert pages == [1, 2]
    assert headers_used[0]['Authorization'] == 'token T'
    assert items == [{'page': 1}, {'page': 2}]
    assert '2021-01-01' in queries[0]
