import os
import io
import sys
import time
import re
import pytest

import knucleotide as kn


# -----------------------------
# Defaults: LONG by default
# Disable with: FAST_TEST=1 pytest -q
# Tune with: LONG_REPEATS=200000 (default 200000)
# -----------------------------
FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1", "true", "yes"}
DEFAULT_LONG_REPEATS = int(os.getenv("LONG_REPEATS", "200000"))


# Same translation as main()
TRANSLATION = bytes.maketrans(
    b"GTCAgtca",
    b"\x00\x01\x02\x03\x00\x01\x02\x03",
)


def bits_of(s: str) -> int:
    buf = s.encode("latin1").translate(TRANSLATION)
    bits = 0
    for b in buf:
        bits = bits * 4 + b
    return bits


def as_encoded_sequence(text: str) -> bytearray:
    return bytearray(text.encode("latin1").translate(TRANSLATION))


def capture_print(monkeypatch, func, *args, **kwargs) -> str:
    out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    func(*args, **kwargs)
    return out.getvalue()


def make_reading_frames_small():
    """
    Small frames suitable for very short sequences.
    Avoids the benchmark's long k-mers (length up to 18).
    """
    mono = ("G", "A", "T", "C")
    di = tuple(a + b for a in mono for b in mono)
    frames = [
        (1, tuple(bits_of(x) for x in mono)),
        (2, tuple(bits_of(x) for x in di)),
    ]
    return mono, di, frames


def make_reading_frames_full():
    """
    Same frames as main(): mono, di, plus the specific k-mers.
    """
    mono = ("G", "A", "T", "C")
    di = tuple(a + b for a in mono for b in mono)
    k = ("GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT")
    frames = [
        (1, tuple(bits_of(x) for x in mono)),
        (2, tuple(bits_of(x) for x in di)),
    ] + [(len(s), (bits_of(s),)) for s in k]
    return mono, di, k, frames


# -----------------------------
# Unit tests
# -----------------------------
def test_read_sequence_picks_three_record():
    fasta = (
        b">ONE\nAAAA\n"
        b">THREE\nGgTtAaCc\n"
        b">FOUR\nCCCC\n"
    )
    f = io.BytesIO(fasta)
    seq = kn.read_sequence(f, b"THREE", TRANSLATION)
    assert isinstance(seq, (bytes, bytearray))
    assert len(seq) == 8
    assert set(seq) <= {0, 1, 2, 3}


def test_count_frequencies_simple_known_counts():
    # Use only frames 1 and 2 for a short sequence.
    mono, di, reading_frames = make_reading_frames_small()
    seq = as_encoded_sequence("GATTACA")  # length 7
    results = kn.count_frequencies(seq, reading_frames, 0, len(seq))

    # mono counts: G=1, A=3, T=2, C=1
    expected_mono = {"G": 1, "A": 3, "T": 2, "C": 1}
    for base, expected in expected_mono.items():
        bits = bits_of(base)
        freq, n = kn.lookup_frequency(results, 1, bits)
        assert freq == expected
        assert n == len(seq)

    # di counts windows: GA, AT, TT, TA, AC, CA each once
    expected_di = {"GA": 1, "AT": 1, "TT": 1, "TA": 1, "AC": 1, "CA": 1}
    for dimer, expected in expected_di.items():
        bits = bits_of(dimer)
        freq, n = kn.lookup_frequency(results, 2, bits)
        assert freq == expected
        assert n == len(seq) - 2 + 1  # 6


def test_display_formats_relative(monkeypatch):
    mono, di, reading_frames = make_reading_frames_small()
    seq = as_encoded_sequence("GATTACA")
    results = kn.count_frequencies(seq, reading_frames, 0, len(seq))

    display_list = [(b, 1, bits_of(b)) for b in mono]
    out = capture_print(monkeypatch, kn.display, results, display_list, sort=True, relative=True)

    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    assert len(lines) >= 4
    assert re.match(r"^[GATC] \d+\.\d{3}$", lines[0])


# -----------------------------
# main() integration test
# -----------------------------
def test_main_small_end_to_end(monkeypatch):
    # Provide a FASTA with THREE record long enough for the biggest k-mer (18).
    # Use a repeated pattern that contains GGT... so k-mers appear.
    three_seq = (b"GGTATTTTAATTTATAGT" * 20) + b"\n"
    fasta = b">THREE\n" + three_seq + b">OTHER\nAAAA\n"

    class _FakeStdin:
        def __init__(self, data: bytes):
            self.buffer = io.BytesIO(data)

    monkeypatch.setattr(kn, "stdin", _FakeStdin(fasta))

    out = capture_print(monkeypatch, kn.main)

    lines = [ln.rstrip("\n") for ln in out.splitlines()]
    tab_lines = [ln for ln in lines if "\t" in ln]

    # last section prints 5 lines: "<count>\t<kmer>"
    assert len(tab_lines) == 5
    assert any(ln.endswith("\tGGT") for ln in tab_lines)
    assert any(ln.endswith("\tGGTA") for ln in tab_lines)


# -----------------------------
# Long test (DEFAULT ON)
# -----------------------------
def test_long_counting_default():
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    # Longer by default:
    repeats = int(os.getenv("LONG_REPEATS", "400000"))   # was 200000
    rounds  = int(os.getenv("LONG_ROUNDS", "2"))         # run counting multiple times
    pattern = "GGTATTTTAATTTATAGT"

    seq = as_encoded_sequence(pattern * repeats)
    mono, di, k, reading_frames = make_reading_frames_full()

    t0 = time.time()
    last_results = None
    for _ in range(rounds):
        last_results = kn.count_frequencies(seq, reading_frames, 0, len(seq))
    dt = time.time() - t0

    # sanity check from the final round
    ggt_bits = bits_of("GGT")
    freq, n = kn.lookup_frequency(last_results, 3, ggt_bits)
    assert freq >= repeats

    # very loose bound for shared machines
    assert dt < 1800
