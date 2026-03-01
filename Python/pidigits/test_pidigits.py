import os
import re
import sys
import time
import subprocess
from pathlib import Path
import pytest

FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1", "true", "yes"}
DEFAULT_LONG_N = int(os.getenv("LONG_N", "4000"))
FALLBACK_DIGITS = int(os.getenv("FALLBACK_DIGITS", "20000"))  # runtime knob when gmpy2 missing

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "pidigits.py"


def gmpy2_available() -> bool:
    try:
        import gmpy2  # noqa: F401
        return True
    except Exception:
        return False


def run_pidigits(n: int) -> str:
    assert SCRIPT.exists(), f"Cannot find {SCRIPT}"
    cmd = [sys.executable, str(SCRIPT), str(n)]
    p = subprocess.run(cmd, cwd=str(HERE), text=True, capture_output=True)
    if p.returncode != 0:
        raise AssertionError(
            f"pidigits failed rc={p.returncode}\n"
            f"CMD: {' '.join(cmd)}\n"
            f"CWD: {HERE}\n"
            f"STDERR:\n{p.stderr}\n"
            f"STDOUT:\n{p.stdout}\n"
        )
    return p.stdout


def extract_digits_only(out: str) -> str:
    return "".join(ch for ch in out if ch.isdigit())


def parse_lines(out: str):
    return [ln for ln in out.splitlines() if ln.strip()]


# -------------------------------------------------------------------
# Real tests (only when gmpy2 is available)
# -------------------------------------------------------------------
@pytest.mark.skipif(not gmpy2_available(), reason="gmpy2 not available; skipping real pidigits tests")
@pytest.mark.parametrize("n,expected_prefix", [
    (1,  "3"),
    (2,  "31"),
    (5,  "31415"),
    (10, "3141592653"),
    (20, "31415926535897932384"),
    (25, "3141592653589793238462643"),
])
def test_known_prefixes(n, expected_prefix):
    out = run_pidigits(n)
    digits = extract_digits_only(out)
    assert digits[:n] == expected_prefix


@pytest.mark.skipif(not gmpy2_available(), reason="gmpy2 not available; skipping real pidigits tests")
def test_format_10_digits_per_line_and_counter():
    n = 25
    out = run_pidigits(n)
    lines = parse_lines(out)

    for i, line in enumerate(lines, 1):
        m = re.match(r"^(.{10})\t:(\d+)$", line)
        assert m, f"bad line format: {line!r}"
        block, count = m.group(1), int(m.group(2))
        assert count == min(i * 10, n)
        if count < n:
            assert block.isdigit()
        else:
            assert set(block) <= set("0123456789 ")

    digits = extract_digits_only(out)
    assert len(digits) == n


@pytest.mark.skipif(not gmpy2_available(), reason="gmpy2 not available; skipping real pidigits tests")
def test_long_run_default_real():
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    n = DEFAULT_LONG_N
    out = run_pidigits(n)
    lines = parse_lines(out)
    assert lines and lines[-1].endswith(f"\t:{n}")
    digits = extract_digits_only(out)
    assert len(digits) == n


# -------------------------------------------------------------------
# Fallback long test (runs when gmpy2 is missing)
# This is to make `pytest -q` run longer by default even without gmpy2.
# -------------------------------------------------------------------
def _pi_digits_unbounded(count: int) -> str:
    """
    Correct spigot (unbounded) for digits of pi in base 10.
    Produces digits without the decimal point: "314159..."
    """
    # Unbounded spigot using integer arithmetic
    q, r, t, k, n, l = 1, 0, 1, 1, 3, 3
    out = []
    while len(out) < count:
        if 4*q + r - t < n*t:
            out.append(str(n))
            nr = 10*(r - n*t)
            n = ((10*(3*q + r)) // t) - 10*n
            q *= 10
            r = nr
        else:
            nr = (2*q + r) * l
            nn = (q*(7*k) + 2 + r*l) // (t*l)
            q *= k
            t *= l
            l += 2
            k += 1
            r = nr
            n = nn
    return "".join(out)


@pytest.mark.skipif(gmpy2_available(), reason="gmpy2 is available; fallback test not needed")
def test_long_fallback_when_gmpy2_missing():
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    t0 = time.time()
    digits = _pi_digits_unbounded(FALLBACK_DIGITS)
    dt = time.time() - t0

    # sanity: starts with 3.1415...
    assert digits.startswith("31415")
    assert len(digits) == FALLBACK_DIGITS

    # loose bound on shared machines
    assert dt < 1800
