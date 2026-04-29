from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional
from time import time

try:
    from prometheus_client import Counter, Histogram
    _has_prom = True
except Exception:
    _has_prom = False

from .resume_parser import parse_resume

executor = ThreadPoolExecutor(max_workers=4)

if _has_prom:
    PARSE_REQUESTS = Counter("resume_parse_requests_total", "Total resume parse requests")
    PARSE_DURATION = Histogram("resume_parse_duration_seconds", "Resume parse duration seconds")
else:
    class _NoOp:
        def inc(self, *a, **k):
            return None

        def observe(self, *a, **k):
            return None

    PARSE_REQUESTS = _NoOp()
    PARSE_DURATION = _NoOp()


def _run_parse(path: str, add_to_index: bool, resume_id: Optional[str]):
    start = time()
    try:
        result = parse_resume(path, add_to_index=add_to_index, resume_id=resume_id)
        return result
    finally:
        PARSE_DURATION.observe(time() - start)


def enqueue_parse(path: str, add_to_index: bool = False, resume_id: Optional[str] = None) -> Future:
    PARSE_REQUESTS.inc()
    return executor.submit(_run_parse, path, add_to_index, resume_id)
