import os
import re
import sys
import time
import pytest

# CHANGE this import to match your script filename (without .py)
import fasta as fa


# -----------------------------
# Defaults: LONG by default
# Disable with: FAST_TEST=1 pytest -q
# Tune with: LONG_N=25000 (default 25000)
# -----------------------------
FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1", "true", "yes"}
DEFAULT_LONG_N = int(os.getenv("LONG_N", "25000000"))


# -----------------------------
# Helpers
# -----------------------------
DNA_IUB = set("acgtBDHKMNRSVWY")
DNA_HOMO = set("acgt")


def _capture_stdout_bytes(monkeypatch, func, *args, **kwargs) -> bytes:
    """
    Capture sys.stdout.buffer.write output as bytes.
    """
    buf = bytearray()

    class _FakeBuf:
        def write(self, b):
            if isinstance(b, str):
                b = b.encode("utf-8")
            buf.extend(b)
            return len(b)

    class _FakeStdout:
        buffer = _FakeBuf()

    monkeypatch.setattr(sys, "stdout", _FakeStdout())
    func(*args, **kwargs)
    return bytes(buf)


def _parse_fasta_sections(output: bytes):
    """
    Parse output into [(header:str, seq:bytes), ...]
    Header lines begin with '>'.
    Sequence lines are concatenated (newlines removed).
    """
    lines = output.splitlines()
    sections = []
    cur_header = None
    cur_seq = bytearray()
    for ln in lines:
        if ln.startswith(b">"):
            if cur_header is not None:
                sections.append((cur_header, bytes(cur_seq)))
            cur_header = ln.decode("utf-8")
            cur_seq = bytearray()
        else:
            cur_seq.extend(ln.strip())
    if cur_header is not None:
        sections.append((cur_header, bytes(cur_seq)))
    return sections


def _assert_wrapped_60(output: bytes):
    """
    For each sequence block, all lines must be length 60 except maybe last line of the block.
    """
    lines = output.splitlines()
    in_seq = False
    current_block = []
    for ln in lines:
        if ln.startswith(b">"):
            # check previous block
            if current_block:
                for x in current_block[:-1]:
                    assert len(x) == 60
                assert 1 <= len(current_block[-1]) <= 60
            current_block = []
            in_seq = True
        else:
            if in_seq:
                if ln.strip():
                    current_block.append(ln.strip())

    if current_block:
        for x in current_block[:-1]:
            assert len(x) == 60
        assert 1 <= len(current_block[-1]) <= 60


# -----------------------------
# Fast unit tests
# -----------------------------
def test_make_cumulative_monotonic_and_complete():
    probs, chars = fa.make_cumulative(fa.homosapiens)
    assert len(probs) == len(chars) == 4
    assert all(probs[i] > probs[i - 1] for i in range(1, len(probs)))
    assert abs(probs[-1] - 1.0) < 1e-9
    assert set(chr(c) for c in chars) == DNA_HOMO


def test_repeat_fasta_exact_sequence_small(monkeypatch):
    # repeat_fasta prints exactly n bases from repeated src
    src = "abc"
    n = 8  # expect "abcabcab"
    out = _capture_stdout_bytes(monkeypatch, fa.repeat_fasta, src, n)
    seq = b"".join([ln.strip() for ln in out.splitlines() if ln.strip()])
    assert seq == b"abcabcab"


def test_random_fasta_deterministic_seed_and_alphabet(monkeypatch):
    # For a fixed seed and table, output must be deterministic.
    n = 200
    seed0 = 42.0

    out1 = _capture_stdout_bytes(monkeypatch, fa.random_fasta, fa.homosapiens, n, seed0)
    out2 = _capture_stdout_bytes(monkeypatch, fa.random_fasta, fa.homosapiens, n, seed0)

    seq1 = b"".join([ln.strip() for ln in out1.splitlines() if ln.strip()])
    seq2 = b"".join([ln.strip() for ln in out2.splitlines() if ln.strip()])

    assert seq1 == seq2
    assert len(seq1) == n
    assert set(seq1.decode("utf-8")) <= DNA_HOMO


def test_random_fasta_returns_updated_seed(monkeypatch):
    n = 120
    seed0 = 42.0

    # capture output but also check returned seed changes
    buf = bytearray()

    class _FakeBuf:
        def write(self, b):
            buf.extend(b)
            return len(b)

    class _FakeStdout:
        buffer = _FakeBuf()

    monkeypatch.setattr(sys, "stdout", _FakeStdout())
    seed1 = fa.random_fasta(fa.iub, n, seed0)
    assert seed1 != seed0


# -----------------------------
# main() structure test (small)
# -----------------------------
def test_main_small_output_structure(monkeypatch):
    n = 25

    def _run_main():
        fa.main()

    # set argv and capture stdout bytes
    monkeypatch.setattr(sys, "argv", ["fasta.py", str(n)])
    out = _capture_stdout_bytes(monkeypatch, _run_main)

    sections = _parse_fasta_sections(out)
    assert len(sections) == 3
    assert sections[0][0].startswith(">ONE Homo sapiens alu")
    assert sections[1][0].startswith(">TWO IUB ambiguity codes")
    assert sections[2][0].startswith(">THREE Homo sapiens frequency")

    # lengths: alu repeats 2n, iub random 3n, homosapiens random 5n
    assert len(sections[0][1]) == n * 2
    assert len(sections[1][1]) == n * 3
    assert len(sections[2][1]) == n * 5

    # alphabets
    assert set(sections[0][1].decode("utf-8")) <= set("ACGT")  # alu is uppercase
    assert set(sections[1][1].decode("utf-8")) <= DNA_IUB
    assert set(sections[2][1].decode("utf-8")) <= DNA_HOMO

    # wrapping rule: lines are 60 wide except last line per section
    _assert_wrapped_60(out)


# -----------------------------
# Long test (DEFAULT ON)
# -----------------------------
def test_main_long_default(monkeypatch):
    """
    Default-on longer run to exercise performance/logic.
    Disable with FAST_TEST=1.
    """
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    n = DEFAULT_LONG_N
    monkeypatch.setattr(sys, "argv", ["fasta.py", str(n)])

    t0 = time.time()
    out = _capture_stdout_bytes(monkeypatch, fa.main)
    dt = time.time() - t0

    sections = _parse_fasta_sections(out)
    assert len(sections) == 3
    assert len(sections[0][1]) == n * 2
    assert len(sections[1][1]) == n * 3
    assert len(sections[2][1]) == n * 5

    # Keep a loose time bound (shared machine variability)
    assert dt < 900
