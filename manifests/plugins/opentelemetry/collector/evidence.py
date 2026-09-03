"""Lab-only, bounded OTLP JSON summarizer. Never logs request bodies or headers.

Ingestion binds loopback; the ClusterIP exposes only read-only summaries.
Raw spans/attributes are transient in memory, never written to disk.
"""
import json
import re
import threading
import uuid
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

MAX_BODY = 2 * 1024 * 1024
MAX_SPANS = 4000
NAMES = {"kong", "kong.balancer", "kong.router", "kong.dns",
         "kong.access.plugin.opentelemetry", "kong.header_filter.plugin.opentelemetry"}


def identifier(value, length):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{%d}" % length, value):
        raise ValueError("Invalid identifier")
    if int(value, 16) == 0:
        raise ValueError("Zero identifier")
    return value.lower()


def attributes(items):
    # Read only known scalar fields; never echo arbitrary attribute values.
    allowed = {"service.name", "http.method", "http.status_code", "http.route"}
    return {a["key"]: a.get("value", {}).get("stringValue", a.get("value", {}).get("intValue"))
            for a in items if a.get("key") in allowed}


def normalize(payload):
    result = []
    for resource in payload.get("resourceSpans", []):
        if attributes(resource.get("resource", {}).get("attributes", [])).get("service.name") != "kong-otel-lab":
            continue
        for scope in resource.get("scopeSpans", []):
            for span in scope.get("spans", []):
                if span.get("name") not in NAMES:
                    continue
                start = int(span["startTimeUnixNano"])
                end = int(span["endTimeUnixNano"])
                if not 0 < start <= end or end - start > 3600 * 10**9:
                    raise ValueError("Invalid duration")
                attrs = attributes(span.get("attributes", []))
                event = {"trace_id": identifier(span["traceId"], 32),
                         "span_id": identifier(span["spanId"], 16),
                         "parent_id": identifier(span["parentSpanId"], 16) if span.get("parentSpanId") else "",
                         "name": span["name"], "duration_ns": end - start}
                if attrs.get("http.method") == "GET":
                    event["method"] = "GET"
                if attrs.get("http.route") in ("/transform", "/demo", "/demo2"):
                    event["route"] = attrs["http.route"]
                if str(attrs.get("http.status_code")) == "200":
                    event["status"] = 200
                result.append(event)
    return result


class Store:
    def __init__(self, capacity=MAX_SPANS):
        self.events = deque(maxlen=capacity)
        self.instance = uuid.uuid4().hex
        self.evicted = 0
        self.lock = threading.Lock()

    def append(self, events):
        with self.lock:
            self.evicted += max(0, len(self.events) + len(events) - self.events.maxlen)
            self.events.extend(events)

    def snapshot(self, traces):
        with self.lock:
            return {"instance": self.instance, "evicted": self.evicted,
                    "events": [e for e in self.events if e["trace_id"] in traces]}


STORE = Store()


class BaseHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def respond(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class IngestHandler(BaseHandler):
    def do_POST(self):
        try:
            if self.path != "/v1/traces":
                return self.respond(404, {})
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BODY:
                return self.respond(413, {})
            if self.headers.get("Content-Encoding", "identity") != "identity":
                return self.respond(415, {})
            events = normalize(json.loads(self.rfile.read(length)))
            STORE.append(events)
            self.respond(200, {})
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
            self.respond(400, {})


class ReadHandler(BaseHandler):
    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == "/healthz":
            return self.respond(200, {"status": "ok"})
        if parsed.path != "/events":
            return self.respond(404, {})
        try:
            values = parse_qs(parsed.query).get("trace", [])
            if not 1 <= len(values) <= 12:
                raise ValueError("Expected bounded trace query")
            traces = {identifier(v, 32) for v in values}
            self.respond(200, STORE.snapshot(traces))
        except ValueError:
            self.respond(400, {})


if __name__ == "__main__":
    ingest = ThreadingHTTPServer(("127.0.0.1", 8081), IngestHandler)
    threading.Thread(target=ingest.serve_forever, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8080), ReadHandler).serve_forever()
