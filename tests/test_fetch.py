# -*- coding: utf-8 -*-
"""fetcher/fetch.py: JSON eilučių protokolas, leidžiami adresai, sesijos."""
import importlib.util
import io
import json
import os
import unittest

_spec = importlib.util.spec_from_file_location(
    "fetch", os.path.join(os.path.dirname(__file__), "..", "fetcher", "fetch.py"))
fetch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fetch)


class FakeResponse:
    def __init__(self, url):
        self.status_code, self.url, self.text, self.headers = 200, url, "ok", {"content-type": "text/plain"}


class FakeSession:
    made = 0

    def __init__(self):
        FakeSession.made += 1
        self.cookies, self.calls = {"a": "1"}, []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(url)
        return FakeResponse(url)


def run(*msgs):
    FakeSession.made = 0
    out = io.StringIO()
    inp = io.StringIO("".join(json.dumps(m) + "\n" for m in msgs))
    result = fetch.serve(inp, out, session_factory=FakeSession, run_id="7")
    return result, [json.loads(l) for l in out.getvalue().splitlines()]


class FetchTest(unittest.TestCase):
    def test_protocol(self):
        (got, errors, done), lines = run({"op": "get", "id": 1, "url": "https://www.vinted.lt/api/v2/x"},
                                         {"op": "done", "fetched": 1})
        self.assertEqual(lines[0], {"hello": 1, "run": "7"})
        self.assertEqual((lines[1]["id"], lines[1]["status"], lines[1]["text"], lines[1]["cookies"]),
                         (1, 200, "ok", {"a": "1"}))
        self.assertEqual((got, errors, done["fetched"]), (1, 0, 1))

    def test_only_vinted(self):
        for url in ("http://www.vinted.lt/", "https://example.com/", "https://vinted.lt.evil.com/",
                    "https://evilvinted.lt/", "file:///etc/passwd"):
            self.assertEqual(fetch.fetch(FakeSession(), {"id": 1, "url": url})["error"], "adresas neleidžiamas", url)
        for url in ("https://www.vinted.lt/", "https://api.vinted.de/", "https://www.vinted.co.uk/"):
            self.assertNotIn("error", fetch.fetch(FakeSession(), {"id": 1, "url": url}), url)

    def test_sessions_by_sid(self):
        u = "https://www.vinted.pl/"
        (got, _, _), _ = run({"op": "get", "id": 1, "sid": "pl", "url": u}, {"op": "get", "id": 2, "sid": "pl", "url": u},
                             {"op": "get", "id": 3, "sid": "de", "url": u}, {"op": "done"})
        self.assertEqual((got, FakeSession.made), (3, 2))

    def test_connection_lost(self):
        (got, errors, done), _ = run({"op": "get", "id": 1, "url": "https://www.vinted.lt/"})
        self.assertIsNone(done)


if __name__ == "__main__":
    unittest.main()
