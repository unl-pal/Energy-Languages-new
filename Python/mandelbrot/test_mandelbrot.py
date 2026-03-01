import os
import io
import sys
import time
import pytest

# CHANGE this import to match your filename (without .py)
import mandelbrot as mb


# -----------------------------
# Defaults: LONG by default
# Disable with: FAST_TEST=1 pytest -q
# Tune with: LONG_N=1200 (default 1200)
# -----------------------------
FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1", "true", "yes"}
DEFAULT_LONG_N = int(os.getenv("LONG_N", "3000"))


# -----------------------------
# Helpers
# -----------------------------
def _capture_stdout_bytes(monkeypatch, func, *args, **kwargs) -> bytes:
    buf = bytearray()

    class _FakeBuf:
        def write(self, b):
            if isinstance(b, str):
                b = b.encode("utf-8")
            buf.extend(b)
            return len(b)

    class _FakeStdout:
        buffer = _FakeBuf()

    monkeypatch.setattr(mb, "stdout", _FakeStdout())
    func(*args, **kwargs)
    return bytes(buf)


def _expected_pbm_size(n: int) -> int:
    # PBM P4: header "P4\n{n} {n}\n" plus n rows of ceil(n/8) bytes
    header = f"P4\n{n} {n}\n".encode()
    row_bytes = (n + 7) // 8
    return len(header) + n * row_bytes


# -----------------------------
# Unit tests
# -----------------------------
def test_pixels_yields_bytes(monkeypatch):
    # ensure generator yields ints 0..255
    gen = mb.pixels(y=0, n=16, abs=abs)
    v1 = next(gen)
    v2 = next(gen)
    assert isinstance(v1, int) and 0 <= v1 <= 255
    assert isinstance(v2, int) and 0 <= v2 <= 255


@pytest.mark.parametrize("n", [1, 2, 7, 8, 9, 15, 16, 17, 31, 32])
def test_compute_row_length_and_mask(n):
    y = 0
    yy, row = mb.compute_row((y, n))
    assert yy == y
    assert isinstance(row, (bytes, bytearray))
    assert len(row) == (n + 7) // 8

    # last byte must have unused low bits cleared (masking behavior)
    if n % 8 != 0:
        unused = 8 - (n % 8)
        # the low 'unused' bits should be 0
        assert (row[-1] & ((1 << unused) - 1)) == 0


def test_ordered_rows_orders_out_of_order_input():
    # feed rows out-of-order and ensure ordered_rows yields y=0..n-1
    n = 5
    rows_in = iter([(3, b"a"), (0, b"b"), (4, b"c"), (1, b"d"), (2, b"e")])
    ordered = list(mb.ordered_rows(rows_in, n))
    assert [y for y, _ in ordered] == list(range(n))


# -----------------------------
# Integration tests
# -----------------------------
@pytest.mark.parametrize("n", [1, 2, 8, 9, 16, 32, 64])
def test_mandelbrot_pbm_header_and_size_single_process(monkeypatch, n):
    # force single-process path
    monkeypatch.setattr(mb, "cpu_count", lambda: 1)

    out = _capture_stdout_bytes(monkeypatch, mb.mandelbrot, n)

    header = f"P4\n{n} {n}\n".encode()
    assert out.startswith(header)
    assert len(out) == _expected_pbm_size(n)

    # body length equals n * ceil(n/8)
    body = out[len(header):]
    assert len(body) == n * ((n + 7) // 8)


def test_mandelbrot_deterministic_single_process(monkeypatch):
    monkeypatch.setattr(mb, "cpu_count", lambda: 1)
    out1 = _capture_stdout_bytes(monkeypatch, mb.mandelbrot, 64)
    out2 = _capture_stdout_bytes(monkeypatch, mb.mandelbrot, 64)
    assert out1 == out2


# -----------------------------
# Long test (DEFAULT ON)
# -----------------------------
def test_long_run_default(monkeypatch):
    """
    Default-on longer test to make `pytest -q` take longer.
    Disable with FAST_TEST=1.
    """
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    monkeypatch.setattr(mb, "cpu_count", lambda: 1)
    n = DEFAULT_LONG_N

    t0 = time.time()
    out = _capture_stdout_bytes(monkeypatch, mb.mandelbrot, n)
    dt = time.time() - t0

    # sanity checks
    header = f"P4\n{n} {n}\n".encode()
    assert out.startswith(header)
    assert len(out) == _expected_pbm_size(n)

    # loose bound for shared machines
    assert dt < 1800
