import os
import re
import time
import itertools
import pytest
from itertools import islice

import fannkuch as fk


# -----------------------------
# Defaults: LONG by default
# Disable with: FAST_TEST=1 pytest -q
# Tune with: LONG_N=12 (default 12)
# -----------------------------
FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1", "true", "yes"}
DEFAULT_LONG_N = int(os.getenv("LONG_N", "10"))


def _parse_output(out: str):
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    assert len(lines) >= 2, f"expected 2+ lines, got {lines!r}"
    checksum = int(lines[-2])
    m = re.match(r"Pfannkuchen\((\d+)\)\s*=\s*(\d+)$", lines[-1])
    assert m, f"unexpected summary line: {lines[-1]!r}"
    return checksum, int(m.group(1)), int(m.group(2))


def _run_fannkuch_capture(monkeypatch, capsys, n: int, force_task_count: int = 1):
    monkeypatch.setattr(fk, "cpu_count", lambda: force_task_count)
    fk.fannkuch(n)
    return capsys.readouterr().out


def _bruteforce_max_flips(n: int) -> int:
    def flips_for_perm(p):
        p = list(p)
        flips = 0
        while True:
            k = p[0]
            if k == 0:
                return flips
            p[:k+1] = reversed(p[:k+1])
            flips += 1

    m = 0
    for perm in itertools.permutations(range(n)):
        f = flips_for_perm(perm)
        if f > m:
            m = f
    return m


def _checksum_via_chunks(n: int, chunk_size: int):
    total = fk.factorial(n)
    assert chunk_size % 2 == 0
    assert total % 2 == 0  # requires n>=2

    checksum = 0
    maximum = 0
    start = 0
    while start < total:
        size = min(chunk_size, total - start)
        if size >= 2 and (size % 2 == 1):
            size -= 1
        if size <= 0:
            break
        c, m = fk.task(n, start, size)
        checksum += c
        maximum = max(maximum, m)
        start += size
    return checksum, maximum


# -----------------------------
# Fast tests (always)
# -----------------------------
def test_permutations_yields_valid_perms_small():
    n = 7
    start = 0
    size = 10
    perms = list(islice(fk.permutations(n, start, size), size))
    assert len(perms) == size
    for p in perms:
        assert len(p) == n
        assert sorted(p) == list(range(n))


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 7])
def test_maximum_matches_bruteforce_for_small_n(monkeypatch, capsys, n):
    out = _run_fannkuch_capture(monkeypatch, capsys, n, force_task_count=1)
    checksum, n_out, maximum = _parse_output(out)
    assert n_out == n
    assert maximum == _bruteforce_max_flips(n)


def test_official_output_for_n7(monkeypatch, capsys):
    # Benchmarks Game reference for n=7: checksum=228, max=16
    out = _run_fannkuch_capture(monkeypatch, capsys, 7, force_task_count=1)
    checksum, n_out, maximum = _parse_output(out)
    assert (checksum, n_out, maximum) == (228, 7, 16)


def test_checksum_consistent_across_chunk_sizes():
    n = 10
    total = fk.factorial(n)
    assert total % 2 == 0

    c1, m1 = fk.task(n, 0, total)
    c2, m2 = _checksum_via_chunks(n, chunk_size=20000)

    assert c2 == c1
    assert m2 == m1


def test_negative_prints_all_perms_set(capsys):
    fk.fannkuch(-3)
    out = [ln.strip() for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert len(out) == 6
    assert set(out) == {"123", "132", "213", "231", "312", "321"}


# -----------------------------
# Long tests (DEFAULT ON)
# -----------------------------
def test_long_run_default_single_process(monkeypatch, capsys):
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    n = DEFAULT_LONG_N
    # n must be >=2 for this implementation to satisfy even task_size constraints
    assert n >= 2

    t0 = time.time()
    out = _run_fannkuch_capture(monkeypatch, capsys, n, force_task_count=1)
    dt = time.time() - t0

    checksum, n_out, maximum = _parse_output(out)
    assert n_out == n
    assert isinstance(checksum, int)
    assert maximum >= 0
    assert dt < 900


class _FakePool:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def starmap(self, fn, iterable):
        return [fn(*args) for args in iterable]


def test_pool_branch_without_forking(monkeypatch, capsys):
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    monkeypatch.setattr(fk, "cpu_count", lambda: 4)
    monkeypatch.setattr(fk, "Pool", lambda: _FakePool())

    n = int(os.getenv("POOL_TEST_N", "10"))
    assert n >= 2
    fk.fannkuch(n)
    out = capsys.readouterr().out
    checksum, n_out, maximum = _parse_output(out)
    assert n_out == n
    assert maximum == _bruteforce_max_flips(n)
