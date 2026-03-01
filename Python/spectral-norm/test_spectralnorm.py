import os
import io
import sys
import math
import pytest

import spectralnorm as sn

FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1", "true", "yes"}
DEFAULT_LONG_N = int(os.getenv("LONG_N", "1000"))


class FakePool:
    def map(self, fn, iterable):
        return list(map(fn, iterable))


def run_main_capture(monkeypatch, n: int) -> str:
    """
    Run sn.main() with argv patched and a deterministic in-process pool.
    """
    # pool is only created under __main__ in the benchmark, so create it for tests.
    monkeypatch.setattr(sn, "pool", FakePool(), raising=False)
    monkeypatch.setattr(sn, "argv", ["spectralnorm.py", str(n)])

    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    sn.main()
    return buf.getvalue().strip()


def test_eval_A_basic():
    a00 = sn.eval_A(0, 0)
    a01 = sn.eval_A(0, 1)
    a10 = sn.eval_A(1, 0)
    assert a00 == 1.0
    assert 0 < a01 < 1
    assert 0 < a10 < 1
    assert math.isfinite(a01) and math.isfinite(a10)


@pytest.mark.parametrize("n,expected", [
    (1, 1.000000000),
    (2, 1.183350177),
    (3, 1.233644501),
    (5, 1.261217616),
    (10, 1.271844019),
])
def test_main_matches_reference(monkeypatch, n, expected):
    out = run_main_capture(monkeypatch, n)
    val = float(out)

    # allow tiny numeric drift across Python/CPU
    assert abs(val - expected) <= 5e-9

    # formatting: exactly 9 digits after decimal
    assert out == f"{val:.9f}"


def test_long_default(monkeypatch):
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")
    out = run_main_capture(monkeypatch, DEFAULT_LONG_N)
    val = float(out)
    assert 1.0 < val < 2.0
