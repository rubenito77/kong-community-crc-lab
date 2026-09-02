"""Disposable lab sink: bounded memory, no raw bodies or access logs."""
import json
import re
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

EVENTS = deque(maxlen=1000)
LOCK = threading.Lock()
ID = re.compile(r"[a-f0-9]{32}-(?:warmup|target|demo|demo2)-[0-9]+\Z")


def sanitize(event):
    if not isinstance(event, dict) or not ID.fullmatch(str(event.get("lab_id", ""))):
        return None
    request = event.get("request", {})
    path = urlsplit(request.get("uri", "")).path
    if path not in ("/transform", "/demo", "/demo2"):
        return None
    latency = event.get("latencies", {})
    values = {k: latency.get(k) for k in ("kong", "proxy", "request")}
    if any(type(v) not in (int, float) or v < 0 for v in values.values()):
        return None
    status = event.get("response", {}).get("status")
    if type(status) is not int or not 100 <= status <= 599:
        return None
    return {"id": event["lab_id"], "path": path,
            "method": request.get("method") if request.get("method") == "GET" else "OTHER",
            "status": status, "route_present": bool(event.get("route", {}).get("id")),
            "service_present": bool(event.get("service", {}).get("id")), "latencies": values}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def reply(self, code, data):
        body = json.dumps(data, allow_nan=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/healthz":
            return self.reply(200, {"ok": True})
        run = parse_qs(url.query).get("run", [""])[0]
        if url.path != "/events" or not re.fullmatch(r"[a-f0-9]{32}", run):
            return self.reply(400, {"error": "invalid request"})
        with LOCK:
            result = [e for e in EVENTS if e["id"].startswith(run + "-")]
        self.reply(200, result)

    def do_POST(self):
        if self.path != "/logs":
            return self.reply(404, {})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1048576:
                return self.reply(413, {})
            value = json.loads(self.rfile.read(length))
            batch = value if isinstance(value, list) else [value]
            # Build the entire safe batch before modifying shared state.
            safe = [clean for e in batch if (clean := sanitize(e)) is not None]
            json.dumps(safe, allow_nan=False)
        except (ValueError, TypeError, AttributeError, OSError):
            return self.reply(400, {"error": "invalid event"})
        with LOCK:
            EVENTS.extend(safe)
        self.reply(200, {"accepted": len(safe)})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
