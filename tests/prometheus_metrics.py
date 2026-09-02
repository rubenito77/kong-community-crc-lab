"""P04-01: functional metrics checks; Python standard library only."""
import json
import math
import os
from pathlib import Path
import re
import time
import urllib.request

SAMPLE = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(.*)\})?\s+(\S+)$')
LABEL = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)="((?:\\.|[^"\\])*)"(?:,|$)')
FAMILIES = ('kong_http_requests_total', 'kong_kong_latency_ms_count',
            'kong_upstream_latency_ms_count', 'kong_request_latency_ms_count')


def parse(text):
    samples = []
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        match = SAMPLE.fullmatch(line)
        if not match:
            raise ValueError('Invalid metric sample: ' + line[:120])
        name, raw, value = match.groups()
        labels = {}
        pos = 0
        raw = raw or ''
        for item in LABEL.finditer(raw):
            if item.start() != pos:
                raise ValueError('Invalid metric labels')
            labels[item[1]] = json.loads('"' + item[2] + '"')
            pos = item.end()
        if pos != len(raw):
            raise ValueError('Invalid metric labels')
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Non-finite sample')
        samples.append((name, labels, number))
    return samples


def totals(samples, route_prefix):
    result = dict.fromkeys(FAMILIES, 0.0)
    for name, labels, value in samples:
        if name not in result or not labels.get('route', '').startswith(route_prefix):
            continue
        if name == FAMILIES[0] and labels.get('code') != '200':
            continue
        result[name] += value
    return result


def main():
    proxy = os.environ['KONG_PROXY_URL'].rstrip('/')
    metrics = os.environ['METRICS_URL']
    evidence = Path(os.environ['EVIDENCE_DIR'])
    evidence.mkdir(parents=True, exist_ok=True)
    phase = os.environ.get('PHASE', 'test')
    target = 'kong-demo.kong-transform-echo.'
    controls = ('kong-demo.kong-echo.', 'kong-demo.kong-echo-2.')
    report = evidence / (phase + '-results.txt')

    def log(message):
        print(message, flush=True)
        with report.open('a', encoding='utf-8') as out:
            out.write(message + '\n')

    def request(url):
        with urllib.request.urlopen(url, timeout=15) as response:
            assert response.status == 200, 'Expected HTTP 200: ' + url
            return response.read().decode('utf-8'), response.headers

    def scrape(label):
        body, headers = request(metrics)
        assert 'text/plain' in headers.get('Content-Type', ''), 'Unexpected metrics format'
        samples = parse(body)
        assert any(n == 'kong_node_info' for n, _, _ in samples), 'Missing node identity'
        (evidence / (label + '.prom')).write_text(body, encoding='utf-8')
        return samples

    def identities(samples):
        return {(x['node_id'], x.get('version')) for n, x, _ in samples if n == 'kong_node_info'}

    for path in ('transform', 'demo', 'demo2'):
        request(proxy + '/' + path)
        log('baseline /' + path + ' status=200')
    before = scrape(phase + '-before')
    identity = identities(before)
    assert len(identity) == 1, 'This test requires exactly one Gateway replica'
    if phase == 'baseline':
        log('PASS: routes and metrics endpoint reachable before configuration')
        return

    # Wait for KIC reconciliation and asynchronous metric publication.
    for attempt in range(30):
        request(proxy + '/transform')
        time.sleep(2)
        current = scrape('warmup')
        assert identities(current) == identity, 'Gateway changed during test'
        if all(v > 0 for v in totals(current, target).values()):
            break
    else:
        raise AssertionError('Target HTTP/latency series missing after 60 seconds')

    before = current
    # Keep the actual post-warmup baseline used for delta comparisons.
    (evidence / 'test-before.prom').write_text(
        (evidence / 'warmup.prom').read_text(encoding='utf-8'), encoding='utf-8')
    count = 10
    for _ in range(count):
        request(proxy + '/transform')
    for path in ('demo', 'demo2'):
        for _ in range(3):
            request(proxy + '/' + path)
        log('control=/' + path + ' status=200')

    initial = totals(before, target)
    for attempt in range(30):
        time.sleep(2)
        after = scrape('after')
        assert identities(after) == identity, 'Gateway changed during test'
        delta = {k: totals(after, target)[k] - initial[k] for k in FAMILIES}
        if all(v >= count for v in delta.values()):
            break
    else:
        raise AssertionError('Missing expected metric increments: ' + repr(delta))
    for prefix in controls:
        assert totals(after, prefix) == totals(before, prefix), 'Control route was instrumented'
    for family, value in delta.items():
        log(f'{family} target_delta={value:g} expected_min={count}')
    # Histogram buckets and sums must be present for the same target route.
    for family in FAMILIES[1:]:
        base = family.removesuffix('_count')
        for suffix in ('_bucket', '_sum'):
            assert any(n == base + suffix and x.get('route', '').startswith(target)
                       for n, x, _ in after), 'Missing histogram ' + base + suffix
    log('PASS: HTTP counter and latency histograms increased; controls isolated')


if __name__ == '__main__':
    main()
