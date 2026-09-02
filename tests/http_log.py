"""Bounded asynchronous delivery test; writes only allowlisted evidence."""
import json
import os
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen


def get(url, marker=None):
    headers = {"X-Lab-Http-Log-Id": marker} if marker else {}
    with urlopen(Request(url, headers=headers), timeout=5) as response:
        return response.status, response.read(1048576)


def verify(events, expected):
    indexed = {e["id"]: e for e in events}
    for marker, path in expected.items():
        if marker not in indexed:
            return False
        e = indexed[marker]
        assert e["path"] == path and e["method"] == "GET" and e["status"] == 200
        assert e["route_present"] and e["service_present"]
        assert all(type(e["latencies"][k]) in (int, float) and e["latencies"][k] >= 0
                   for k in ("kong", "proxy", "request"))
    return True


def main():
    proxy = os.environ["KONG_PROXY_URL"].rstrip("/")
    sink = os.environ["RECEIVER_URL"].rstrip("/")
    root = Path(os.environ["EVIDENCE_DIR"])
    root.mkdir(parents=True, exist_ok=True)
    run = uuid.uuid4().hex
    assert get(sink + "/healthz")[0] == 200
    for path in ("transform", "demo", "demo2"):
        assert get(proxy + "/" + path)[0] == 200
        print(f"baseline /{path} status=200", flush=True)
    if os.environ.get("PHASE") == "baseline":
        print("PASS: routes and receiver reachable")
        return

    def events():
        return json.loads(get(sink + "/events?run=" + run)[1])

    # KIC convergence: each retry uses a different marker; not counted as test traffic.
    ready = False
    for i in range(30):
        marker = f"{run}-warmup-{i}"
        assert get(proxy + "/transform", marker)[0] == 200
        time.sleep(1)
        if any(e["id"].startswith(run + "-warmup-") for e in events()):
            ready = True
            break
    assert ready, "No HTTP log event after convergence timeout"
    expected = {f"{run}-target-{i}": "/transform" for i in range(5)}
    for marker, path in expected.items():
        assert get(proxy + path, marker)[0] == 200
    controls = {f"{run}-{p}-0" for p in ("demo", "demo2")}
    for path in ("demo", "demo2"):
        assert get(proxy + "/" + path, f"{run}-{path}-0")[0] == 200
        print(f"control=/{path} status=200", flush=True)
    deadline = time.monotonic() + 45
    received = False
    while time.monotonic() < deadline:
        snapshot = events()
        assert not controls.intersection(e["id"] for e in snapshot), "Control route logged"
        received = verify(snapshot, expected) or received
        time.sleep(1)
    assert received, "Missing or invalid target events"
    summary = {"target_events": len(expected), "controls_logged": 0,
               "observation_seconds": 45, "result": "PASS"}
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("target events=5 method=GET status=200 route/service/latencies=valid")
    print("PASS: HTTP events correlated; controls isolated during 45s observation")


if __name__ == "__main__":
    main()
