import unittest
import tempfile
from unittest.mock import patch
from prometheus_metrics import parse, totals, FAMILIES, main


class MetricsTests(unittest.TestCase):
    def test_labels_order_and_code_filter(self):
        data = '''# TYPE kong_http_requests_total counter
kong_http_requests_total{code="200",route="kong-demo.kong-transform-echo.0.0",service="s"} 12
kong_http_requests_total{route="kong-demo.kong-transform-echo.0.0",code="500"} 2
kong_http_requests_total{route="kong-demo.kong-echo.0.0",code="200"} 99
kong_kong_latency_ms_count{route="kong-demo.kong-transform-echo.0.0"} 12
'''
        values = totals(parse(data), 'kong-demo.kong-transform-echo.')
        self.assertEqual(values[FAMILIES[0]], 12)
        self.assertEqual(values[FAMILIES[1]], 12)
        self.assertEqual(values[FAMILIES[2]], 0)

    def test_invalid_input(self):
        for bad in ('not a metric', 'metric{bad} 1', 'metric NaN'):
            with self.assertRaises(ValueError):
                parse(bad)

    def test_histogram_and_unlabelled(self):
        samples = parse('x_bucket{le="+Inf"} 10\nx 1e2\n')
        self.assertEqual(samples[0][1]['le'], '+Inf')
        self.assertEqual(samples[1][2], 100)

    def simulate(self, leak=False, frozen=False, restart=False):
        counts = {'transform': 0, 'demo': 0, 'demo2': 0}
        scrapes = 0

        class Response:
            status = 200
            headers = {'Content-Type': 'text/plain; charset=UTF-8'}

            def __init__(self, text):
                self.text = text

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return self.text.encode()

        def fetch(url, timeout):
            nonlocal scrapes
            if url.endswith('/metrics'):
                scrapes += 1
                node = 'new' if restart and scrapes > 1 else 'original'
                lines = [f'kong_node_info{{node_id="{node}",version="3.9.3"}} 1']
                for path, count in counts.items():
                    if path != 'transform' and not leak:
                        continue
                    route = {'transform': 'kong-transform-echo', 'demo': 'kong-echo',
                             'demo2': 'kong-echo-2'}[path]
                    labels = f'route="kong-demo.{route}.0.0"'
                    count = min(count, 1) if frozen else count
                    for family in FAMILIES:
                        extra = ',code="200"' if family == FAMILIES[0] else ''
                        lines.append(f'{family}{{{labels}{extra}}} {count}')
                    for family in FAMILIES[1:]:
                        base = family.removesuffix('_count')
                        lines.append(f'{base}_bucket{{{labels},le="+Inf"}} {count}')
                        lines.append(f'{base}_sum{{{labels}}} 0')
                return Response('\n'.join(lines))
            counts[url.rsplit('/', 1)[1]] += 1
            return Response('{}')

        with tempfile.TemporaryDirectory() as directory:
            env = {'KONG_PROXY_URL': 'http://proxy', 'METRICS_URL': 'http://metrics/metrics',
                   'EVIDENCE_DIR': directory, 'PHASE': 'test'}
            with patch.dict('os.environ', env), patch('urllib.request.urlopen', fetch), \
                    patch('time.sleep'), patch('builtins.print'):
                main()

    def test_full_flow(self):
        self.simulate()

    def test_reject_instrumented_control(self):
        with self.assertRaisesRegex(AssertionError, 'Control route'):
            self.simulate(leak=True)

    def test_reject_static_counters(self):
        with self.assertRaisesRegex(AssertionError, 'Missing expected metric increments'):
            self.simulate(frozen=True)

    def test_reject_gateway_change(self):
        with self.assertRaisesRegex(AssertionError, 'Gateway changed'):
            self.simulate(restart=True)


if __name__ == '__main__':
    unittest.main()
