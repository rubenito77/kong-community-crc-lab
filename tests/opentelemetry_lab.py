"""Kong 3.9 OTLP integration test. Standard library only; bounded observation."""
import json
import os
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def get(url, trace=None, parent=None):
    headers = {"traceparent": f"00-{trace}-{parent}-01"} if trace else {}
    with urlopen(Request(url, headers=headers), timeout=5) as response:
        data = response.read(2 * 1024 * 1024 + 1)
        assert len(data) <= 2 * 1024 * 1024, "Response too large"
        return response.status, data


def verify(events, expected, controls):
    assert not controls.intersection(e["trace_id"] for e in events), "Control route exported"
    complete = True
    for trace, parent in expected.items():
        spans = {e["span_id"]: e for e in events if e["trace_id"] == trace}
        roots = [s for s in spans.values() if s["name"] == "kong"]
        if not roots:
            complete = False
            continue
        assert len(roots) == 1, "Ambiguous root span"
        root = roots[0]
        assert root["parent_id"] == parent, "W3C parent not preserved"
        assert root.get("method") == "GET" and root.get("status") == 200
        assert root.get("route") == "/transform", "Root route missing, unsupported or not /transform"
        assert root["duration_ns"] > 0
        children = [s for s in spans.values() if s["name"] == "kong.balancer"]
        if not children:
            complete = False
            continue
        assert all(s["parent_id"] == root["span_id"] and s["duration_ns"] > 0 for s in children)
    return complete


def observe(fetch, expected, controls, baseline, seconds=45):
    deadline = time.monotonic() + seconds
    complete = False
    while True:
        snapshot = fetch()
        assert snapshot["instance"] == baseline["instance"], "Evidence sidecar restarted"
        assert snapshot["evicted"] == baseline["evicted"], "Evidence buffer lost spans"
        complete = verify(snapshot["events"], expected, controls) or complete
        if time.monotonic() >= deadline:
            break
        time.sleep(1)
    assert complete, "Expected correlated root/balancer spans missing"


def main():
    proxy = os.environ["KONG_PROXY_URL"].rstrip("/")
    evidence = os.environ["EVIDENCE_URL"].rstrip("/")
    assert get(evidence + "/healthz")[0] == 200
    for path in ("transform", "demo", "demo2"):
        assert get(proxy + "/" + path)[0] == 200
        print(f"baseline /{path} status=200", flush=True)
    if os.environ.get("PHASE") == "baseline":
        print("PASS: routes and evidence endpoint reachable")
        return

    # Separate warmup trace IDs: no counting unconfigured requests as test cases.
    ready = False
    warmup = []
    for _ in range(30):
        trace, parent = uuid.uuid4().hex, uuid.uuid4().hex[:16]
        warmup = (warmup + [trace])[-12:]
        assert get(proxy + "/transform", trace, parent)[0] == 200
        time.sleep(1)
        query = urlencode([("trace", t) for t in warmup])
        snapshot = json.loads(get(evidence + "/events?" + query)[1])
        if any(s["name"] == "kong" for s in snapshot["events"]):
            ready = True
            break
    assert ready, "No root span: check KIC, tracing variables and Collector"

    expected = {uuid.uuid4().hex: uuid.uuid4().hex[:16] for _ in range(5)}
    control_traces = {path: uuid.uuid4().hex for path in ("demo", "demo2")}
    query = urlencode([("trace", t) for t in [*expected, *control_traces.values()]])

    def fetch():
        return json.loads(get(evidence + "/events?" + query)[1])

    baseline = fetch()
    assert not baseline["events"], "Trace IDs already exist"
    for trace, parent in expected.items():
        assert get(proxy + "/transform", trace, parent)[0] == 200
    for path, trace in control_traces.items():
        assert get(proxy + "/" + path, trace, uuid.uuid4().hex[:16])[0] == 200
        print(f"control=/{path} status=200", flush=True)
    observe(fetch, expected, set(control_traces.values()), baseline)
    root = Path(os.environ["EVIDENCE_DIR"])
    root.mkdir(parents=True, exist_ok=True)
    summary = {"result": "PASS", "target_traces": 5, "w3c_parent_preserved": True,
               "root_and_balancer_durations_positive": True, "controls_exported": 0,
               "observation_seconds": 45}
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("target traces=5 W3C parent=valid root/balancer durations=positive")
    print("PASS: OTLP traces correlated; controls isolated during 45s observation")


if __name__ == "__main__":
    main()
