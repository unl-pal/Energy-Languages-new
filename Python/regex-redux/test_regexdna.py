import os
import io
import sys
import re
import pytest

# CHANGE this to match your filename (without .py)
import regexredux as rd


# -----------------------------
# Defaults: LONG by default
# Disable with: FAST_TEST=1 pytest -q
# Tune with: LONG_REPEATS=80000 (default 80000)
# -----------------------------
FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1", "true", "yes"}
DEFAULT_LONG_REPEATS = int(os.getenv("LONG_REPEATS", "8000000"))


VARIANTS = (
    'agggtaaa|tttaccct',
    '[cgt]gggtaaa|tttaccc[acg]',
    'a[act]ggtaaa|tttacc[agt]t',
    'ag[act]gtaaa|tttac[agt]ct',
    'agg[act]taaa|ttta[agt]cct',
    'aggg[acg]aaa|ttt[cgt]ccct',
    'agggt[cgt]aa|tt[acg]accct',
    'agggta[cgt]a|t[acg]taccct',
    'agggtaa[cgt]|[acg]ttaccct',
)

SUBST = {
    'tHa[Nt]': '<4>',
    'aND|caN|Ha[DS]|WaS': '<3>',
    'a[NSt]|BY': '<2>',
    '<[^>]*>': '|',
    '\\|[^|][^|]*\\|': '-',
}


# -----------------------------
# Helpers
# -----------------------------
class FakePool:
    """In-process stand-in for multiprocessing.Pool."""
    def __init__(self, initializer=None, initargs=()):
        if initializer is not None:
            initializer(*initargs)

    def imap(self, fn, iterable):
        for x in iterable:
            yield fn(x)


def make_fasta(seq: str, header: str = "SEQ") -> str:
    # Include FASTA header and line breaks
    # Wrap sequence at 60 chars to look realistic
    lines = [seq[i:i+60] for i in range(0, len(seq), 60)]
    return f">{header}\n" + "\n".join(lines) + "\n"


def run_main_capture(monkeypatch, input_text: str) -> str:
    # Patch stdin.read()
    monkeypatch.setattr(rd, "stdin", io.StringIO(input_text))
    # Patch Pool to avoid forking
    monkeypatch.setattr(rd, "Pool", FakePool)

    out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    rd.main()
    return out.getvalue()


def reference_counts(clean_seq: str):
    return [len(re.findall(pat, clean_seq)) for pat in VARIANTS]


def reference_subst(clean_seq: str) -> str:
    s = clean_seq
    for f, r in list(SUBST.items()):
        s = re.sub(f, r, s)
    return s


def strip_fasta(raw: str) -> str:
    # same as program: remove headers + newlines
    return re.sub('>.*\n|\n', '', raw)


# -----------------------------
# Fast tests
# -----------------------------
def test_strip_fasta_matches_program_logic():
    raw = ">X\nACGT\n>Y\nTT\n"
    cleaned = strip_fasta(raw)
    assert cleaned == "ACGTTT"


def test_variant_counts_match_reference(monkeypatch):
    # Build a small sequence that contains matches
    core = "agggtaaaTTTACCCTagggtaaa"
    # keep lowercase like benchmark expects for patterns
    seq = (core.lower() * 50)
    raw = make_fasta(seq, "THREE")

    output = run_main_capture(monkeypatch, raw)

    cleaned = strip_fasta(raw)
    ref = reference_counts(cleaned)

    # First 9 lines: "<pattern> <count>"
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    first9 = lines[:9]
    assert len(first9) == 9

    for i, line in enumerate(first9):
        pat, count = line.rsplit(" ", 1)
        assert pat == VARIANTS[i]
        assert int(count) == ref[i]


def test_lengths_reported_are_consistent(monkeypatch):
    seq = ("agggtaaa" * 1000).lower()
    raw = make_fasta(seq, "THREE")

    output = run_main_capture(monkeypatch, raw)
    cleaned = strip_fasta(raw)
    substituted = reference_subst(cleaned)

    # Last 3 printed numbers (ilen, clen, len(substituted))
    tail = [ln.strip() for ln in output.splitlines() if ln.strip()][-3:]
    ilen = int(tail[0])
    clen = int(tail[1])
    slen = int(tail[2])

    assert ilen == len(raw)
    assert clen == len(cleaned)
    assert slen == len(substituted)


# -----------------------------
# Long test (DEFAULT ON)
# -----------------------------
def test_long_default(monkeypatch):
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    # Make input big enough to run noticeably longer
    repeats = DEFAULT_LONG_REPEATS
    seq = ("agggtaaa" * repeats).lower()
    raw = make_fasta(seq, "THREE")

    output = run_main_capture(monkeypatch, raw)

    # sanity: should still print 9 variant lines and 3 length lines
    lines = [ln.strip() for ln in output.splitlines()]
    # at least 9 + blank + 3 lines
    assert sum(1 for ln in lines if ln and not ln.isdigit()) >= 9
    nums = [ln for ln in lines if ln.isdigit()]
    assert len(nums) >= 3
