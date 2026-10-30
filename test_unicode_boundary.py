"""Malformed JSON string data must never poison a saved delivery record.

These are deterministic regression cases, not model-quality measurements.
"""
from contextlib import closing
import http.client
import json
import tempfile
import threading
import unittest

import scopeproof_bridge as bridge
from app import create_server
from workflow import Workspace


class UnicodeJSONTests(unittest.TestCase):
    def test_lone_surrogate_values_are_rejected(self):
        for value in ("\ud800", "\udfff", "prefix\udc00suffix", "\ud800\ud800"):
            with self.subTest(value=ascii(value)):
                with self.assertRaisesRegex(bridge.Blocked, "INVALID_JSON"):
                    bridge.parse_json(json.dumps({"nested": [value]}).encode())

    def test_lone_surrogate_keys_are_rejected(self):
        with self.assertRaisesRegex(bridge.Blocked, "INVALID_JSON"):
            bridge.parse_json(b'{"nested":[{"\\ud800":"ordinary value"}]}')

    def test_valid_supplementary_characters_and_accents_are_exact(self):
        value = {"\U0001f642": ["Español — 中文", "\U0001f600", "e\u0301", "\ufffd"]}
        for ensure_ascii in (False, True):
            with self.subTest(ensure_ascii=ensure_ascii):
                self.assertEqual(bridge.parse_json(json.dumps(value, ensure_ascii=ensure_ascii).encode()), value)

    def test_literal_backslash_surrogate_text_is_not_rejected(self):
        value = {"reason": r"The file literally contains \ud800"}
        self.assertEqual(bridge.parse_json(json.dumps(value).encode()), value)


class UnicodeHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ws = Workspace(self.temp.name)
        self.server = create_server(self.ws)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)
        self.temp.cleanup()

    def request(self, path, payload=None):
        headers = {"Authorization": "Bearer " + self.ws.owner_token}
        body = None
        if payload is not None:
            body = json.dumps(payload).encode()
            headers.update({"Origin": self.server.origin, "X-ScopeProof-Request": "1",
                            "Content-Type": "application/json"})
        with closing(http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=4)) as conn:
            conn.request("POST" if payload is not None else "GET", path, body, headers)
            response = conn.getresponse()
            return response.status, json.loads(response.read())

    def package(self, reason="Valid previous review"):
        state = self.ws.state(self.ws.owner_token)
        return {"snapshot": state["snapshot"], "analysis": {"criteria": [
            dict(criterion_id=k, status="unclear", evidence_id=None, quote=None, reason=reason)
            for k in state["criteria"]]}}

    def assert_rejected_without_mutation(self, path, payload):
        prior = self.ws.read()
        status, response = self.request(path, payload)
        self.assertEqual(status, 400)
        self.assertEqual(response, {"error": "INVALID_JSON"})
        self.assertEqual(self.ws.read(), prior)
        self.assertEqual(self.request("/api/delivery-report")[0], 200)

    def test_import_surrogate_reason_preserves_previous_review_and_export(self):
        valid = self.package()
        self.assertEqual(self.request("/api/import-analysis", {"package_text": json.dumps(valid)})[0], 200)
        for bad in ("\ud800", "\udfff"):
            with self.subTest(reason=ascii(bad)):
                malformed = self.package(bad)
                self.assert_rejected_without_mutation("/api/import-analysis", {"package_text": json.dumps(malformed)})
        restarted = Workspace(self.temp.name)
        self.assertEqual(restarted.read(), self.ws.read())
        self.assertIn("html", restarted.delivery_report(restarted.owner_token))

    def test_outer_package_text_surrogate_is_rejected(self):
        self.assert_rejected_without_mutation("/api/import-analysis", {"package_text": "\ud800"})

    def test_evidence_surrogate_is_rejected_before_encoding(self):
        self.assert_rejected_without_mutation("/api/evidence", {
            "revision": 1, "artifacts": {"acceptance-report": "\ud800"}})

    def test_scope_surrogate_is_rejected_before_persistence(self):
        state = self.ws.state(self.ws.owner_token)
        criteria = dict(state["criteria"])
        criteria["responsive"] = "\ud800"
        self.assert_rejected_without_mutation("/api/scope", {
            "revision": 1, "name": "Web studio", "amount_cents": 12500,
            "currency": "EUR", "criteria": criteria})

    def test_valid_emoji_evidence_quote_reason_and_export_remain_exact(self):
        text = "Revisión 🙂: diseño verificado — 中文 e\u0301"
        status, state = self.request("/api/evidence", {
            "revision": 1, "artifacts": {"acceptance-report": text}})
        self.assertEqual(status, 200)
        self.assertEqual(state["artifacts"]["acceptance-report"], text)
        package = self.package(text)
        for row in package["analysis"]["criteria"]:
            row.update(status="evidence_found", evidence_id="acceptance-report", quote=text)
        status, state = self.request("/api/import-analysis", {"package_text": json.dumps(package)})
        self.assertEqual(status, 200)
        self.assertFalse(state["approved_current"])
        self.assertEqual(state["analysis"]["criteria"], package["analysis"]["criteria"])
        status, exported = self.request("/api/delivery-report")
        self.assertEqual(status, 200)
        self.assertIn(text, exported["html"])
        exported["html"].encode("utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
