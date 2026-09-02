import copy
import importlib.util
import json
import threading
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from http_log import verify
import http_log

spec = importlib.util.spec_from_file_location("receiver", Path(__file__).resolve().parents[1] /
    "manifests/plugins/http-log/receiver/receiver.py")
receiver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receiver)
RUN = "a" * 32


def event():
    return {"lab_id": RUN + "-target-0", "request": {"method": "GET", "uri": "/transform?secret=x",
            "headers": {"authorization": "private"}}, "response": {"status": 200},
            "route": {"id": "route"}, "service": {"id": "service"},
            "latencies": {"kong": 0, "proxy": 1, "request": 2}, "consumer": {"secret": "private"}}


class ReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = receiver.ThreadingHTTPServer(("127.0.0.1", 0), receiver.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        receiver.EVENTS.clear()

    def post(self, data):
        return urlopen(Request(self.url + "/logs", data=data,
                       headers={"Content-Type": "application/json"}), timeout=2)

    def test_allowlist(self):
        safe = receiver.sanitize(event())
        self.assertEqual(safe["path"], "/transform")
        self.assertNotIn("private", json.dumps(safe))
        self.assertNotIn("secret", json.dumps(safe))
        self.assertTrue(verify([safe], {RUN + "-target-0": "/transform"}))

    def test_invalid_marker_and_latency(self):
        for field, value in (("lab_id", "secret"), ("latencies", {"kong": -1})):
            data = event()
            data[field] = value
            self.assertIsNone(receiver.sanitize(data))

    def test_object_and_batch(self):
        for data in (event(), [event(), event()]):
            with self.post(json.dumps(data).encode()) as response:
                self.assertEqual(response.status, 200)
        with urlopen(self.url + "/events?run=" + RUN) as response:
            self.assertEqual(len(json.load(response)), 3)

    def test_malformed(self):
        with self.assertRaises(HTTPError) as error:
            self.post(b"not json")
        self.assertEqual(error.exception.code, 400)
        self.assertEqual(len(receiver.EVENTS), 0)

    def test_bound(self):
        receiver.EVENTS.extend([receiver.sanitize(event())] * 1100)
        self.assertEqual(len(receiver.EVENTS), 1000)

    def test_verifier_missing_and_bad_status(self):
        expected = {RUN + "-target-0": "/transform"}
        self.assertFalse(verify([], expected))
        bad = copy.deepcopy(receiver.sanitize(event()))
        bad["status"] = 503
        with self.assertRaises(AssertionError):
            verify([bad], expected)

    def test_full_client_flow_and_control_rejection(self):
        for leak_control in (False, True):
            clock = [0]
            pending = []

            def fake_get(url, marker=None):
                if '/events?' in url:
                    return 200, json.dumps(pending).encode()
                if marker and ('/transform' in url or leak_control):
                    data = event()
                    data['lab_id'] = marker
                    data['request']['uri'] = '/' + url.rsplit('/', 1)[1]
                    pending.append(receiver.sanitize(data))
                return 200, b'{}'

            def sleep(seconds):
                clock[0] += seconds

            with tempfile.TemporaryDirectory() as folder, \
                 patch.dict('os.environ', {'KONG_PROXY_URL': 'http://proxy',
                     'RECEIVER_URL': 'http://sink', 'EVIDENCE_DIR': folder, 'PHASE': 'test'}), \
                 patch.object(http_log, 'get', fake_get), \
                 patch.object(http_log.time, 'sleep', sleep), \
                 patch.object(http_log.time, 'monotonic', lambda: clock[0]):
                if leak_control:
                    with self.assertRaisesRegex(AssertionError, 'Control route logged'):
                        http_log.main()
                else:
                    http_log.main()
                    self.assertEqual(json.loads((Path(folder) / 'summary.json').read_text())['target_events'], 5)


if __name__ == "__main__":
    unittest.main()
