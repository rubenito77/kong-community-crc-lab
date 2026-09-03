import copy
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

import opentelemetry_lab as client

spec = importlib.util.spec_from_file_location("otel_evidence", Path(__file__).resolve().parents[1] /
    "manifests/plugins/opentelemetry/collector/evidence.py")
sink = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sink)
TRACE, ROOT, PARENT, CHILD = "a" * 32, "b" * 16, "c" * 16, "d" * 16


def payload(trace=TRACE, parent=PARENT):
    root = {"traceId": trace, "spanId": ROOT, "parentSpanId": parent, "name": "kong",
            "startTimeUnixNano": "1000000", "endTimeUnixNano": "3000000", "attributes": [
                {"key": "http.method", "value": {"stringValue": "GET"}},
                {"key": "http.status_code", "value": {"intValue": "200"}},
                {"key": "http.route", "value": {"stringValue": "/transform"}},
                {"key": "http.url", "value": {"stringValue": "http://private/?token=SECRET"}},
                {"key": "http.client_ip", "value": {"stringValue": "private"}}]}
    child = {"traceId": trace, "spanId": CHILD, "parentSpanId": ROOT, "name": "kong.balancer",
             "startTimeUnixNano": "1500000", "endTimeUnixNano": "2500000"}
    return {"resourceSpans": [{"resource": {"attributes": [
        {"key": "service.name", "value": {"stringValue": "kong-otel-lab"}}]},
        "scopeSpans": [{"spans": [root, child]}]}]}


class EvidenceTests(unittest.TestCase):
    def test_allowlist_and_correlation(self):
        events = sink.normalize(payload())
        self.assertTrue(client.verify(events, {TRACE: PARENT}, set()))
        for forbidden in ("SECRET", "private", "http.url", "http.client_ip"):
            self.assertNotIn(forbidden, json.dumps(events))

    def test_invalid_identifier_and_duration(self):
        for field, value in (("traceId", "0" * 32), ("traceId", "bad"),
                             ("endTimeUnixNano", "1")):
            data = payload()
            data["resourceSpans"][0]["scopeSpans"][0]["spans"][0][field] = value
            with self.assertRaises(ValueError):
                sink.normalize(data)

    def test_wrong_service_and_unknown_name(self):
        data = payload()
        data["resourceSpans"][0]["resource"]["attributes"][0]["value"]["stringValue"] = "other"
        self.assertEqual(sink.normalize(data), [])
        data = payload()
        data["resourceSpans"][0]["scopeSpans"][0]["spans"][1]["name"] = "SECRET"
        self.assertEqual(len(sink.normalize(data)), 1)

    def test_missing_spans_and_wrong_parent(self):
        events = sink.normalize(payload())
        self.assertFalse(client.verify([], {TRACE: PARENT}, set()))
        self.assertFalse(client.verify(events[:1], {TRACE: PARENT}, set()))
        for index in (0, 1):
            bad = copy.deepcopy(events)
            bad[index]["parent_id"] = "e" * 16
            with self.assertRaises(AssertionError):
                client.verify(bad, {TRACE: PARENT}, set())

    def test_wrong_status_route_and_duration(self):
        for key, value in (("status", 503), ("route", "/demo"), ("duration_ns", 0)):
            events = sink.normalize(payload())
            events[0][key] = value
            with self.assertRaises(AssertionError):
                client.verify(events, {TRACE: PARENT}, set())

    def test_controls_and_duplicates(self):
        events = sink.normalize(payload())
        self.assertTrue(client.verify(events * 2, {TRACE: PARENT}, set()))
        with self.assertRaisesRegex(AssertionError, "Control route"):
            client.verify(events, {}, {TRACE})

    def test_bounded_store(self):
        store = sink.Store(capacity=2)
        store.append(sink.normalize(payload()) * 2)
        snapshot = store.snapshot({TRACE})
        self.assertEqual(snapshot["evicted"], 2)
        self.assertEqual(len(snapshot["events"]), 2)
        self.assertEqual(store.snapshot({"f" * 32})["events"], [])

    def test_observation_checks_last_poll_restart_and_eviction(self):
        baseline = {"instance": "test", "evicted": 0, "events": sink.normalize(payload())}
        for kind in ("control", "restart", "eviction"):
            clock = [0]
            def fetch():
                snapshot = copy.deepcopy(baseline)
                if clock[0] >= 45:
                    if kind == "control":
                        snapshot["events"] += sink.normalize(payload("e" * 32))
                    elif kind == "restart":
                        snapshot["instance"] = "changed"
                    else:
                        snapshot["evicted"] = 1
                return snapshot
            with patch.object(client.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s)), \
                 patch.object(client.time, "monotonic", lambda: clock[0]):
                with self.assertRaises(AssertionError):
                    client.observe(fetch, {TRACE: PARENT}, {"e" * 32}, baseline)

    def test_full_flow_and_summary(self):
        store = sink.Store()
        clock = [0]
        def fake_get(url, trace=None, parent=None):
            if "/events?" in url:
                traces = parse_qs(urlsplit(url).query)["trace"]
                return 200, json.dumps(store.snapshot(set(traces))).encode()
            if trace and url.endswith("/transform"):
                store.append(sink.normalize(payload(trace, parent)))
            return 200, b"{}"
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict("os.environ", {"KONG_PROXY_URL": "http://proxy", "EVIDENCE_URL": "http://sink",
                                      "PHASE": "test", "EVIDENCE_DIR": directory}), \
             patch.object(client, "get", fake_get), \
             patch.object(client.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s)), \
             patch.object(client.time, "monotonic", lambda: clock[0]):
            client.main()
            summary = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(summary["target_traces"], 5)
            self.assertEqual(summary["result"], "PASS")
            self.assertGreaterEqual(clock[0], 45)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servers = [sink.ThreadingHTTPServer(("127.0.0.1", 0), handler)
                       for handler in (sink.IngestHandler, sink.ReadHandler)]
        for server in cls.servers:
            threading.Thread(target=server.serve_forever, daemon=True).start()
        cls.ingest, cls.read = [f"http://127.0.0.1:{s.server_port}" for s in cls.servers]

    @classmethod
    def tearDownClass(cls):
        for server in cls.servers:
            server.shutdown()
            server.server_close()

    def test_http_roundtrip(self):
        sink.STORE = sink.Store()
        with urlopen(Request(self.ingest + "/v1/traces", data=json.dumps(payload()).encode(),
                             headers={"Content-Type": "application/json"})) as response:
            self.assertEqual(json.load(response), {})
        with urlopen(self.read + "/events?trace=" + TRACE) as response:
            self.assertEqual(len(json.load(response)["events"]), 2)

    def test_malformed_and_read_only(self):
        for url, data, status in ((self.ingest + "/v1/traces", b"bad", 400),
                                  (self.read + "/v1/traces", b"{}", 501),
                                  (self.read + "/events?trace=bad", None, 400)):
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(url, data=data))
            self.assertEqual(error.exception.code, status)


if __name__ == "__main__":
    unittest.main()
