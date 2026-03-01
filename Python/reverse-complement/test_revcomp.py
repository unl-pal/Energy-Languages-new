import os
import io
import time
import pytest

import revcomp as rc

FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1","true","yes"}
DEFAULT_LONG_BP = int(os.getenv("LONG_BP", "600000000"))

def make_fasta(records):
    out = bytearray()
    for h, seq in records:
        out += (">" + h + "\n").encode("ascii")
        for i in range(0, len(seq), 60):
            out += (seq[i:i+60] + "\n").encode("ascii")
    return bytes(out)

def parse_fasta_bytes(data: bytes):
    lines = data.splitlines(keepends=True)
    recs = []
    header = None
    seq = bytearray()
    for ln in lines:
        if ln.startswith(b">"):
            if header is not None:
                recs.append((header, bytes(seq).replace(b"\n", b"").replace(b"\r", b"")))
            header = ln
            seq = bytearray()
        else:
            seq.extend(ln)
    if header is not None:
        recs.append((header, bytes(seq).replace(b"\n", b"").replace(b"\r", b"")))
    return recs

def run_single_process_like_main(input_bytes: bytes) -> bytes:
    infile = io.BytesIO(input_bytes)
    out = bytearray()
    for header, seq in rc.read_sequences(infile):
        h, r = rc.reverse_complement(header, seq)
        out.extend(h); out.extend(r)
    return bytes(out)

def revcomp_naive(seq: str) -> str:
    table = bytes.maketrans(
        b'ABCDGHKMNRSTUVWYabcdghkmnrstuvwy',
        b'TVGHCDMKNYSAABWRTVGHCDMKNYSAABWR'
    )
    b = seq.encode("ascii").translate(table)
    return b[::-1].decode("ascii")

def flatten(b: bytes) -> bytes:
    return b.replace(b"\n", b"").replace(b"\r", b"")

def test_read_sequences_parses_multiple_records():
    data = make_fasta([("one","ACGT"), ("two","GATTACA")])
    recs = list(rc.read_sequences(io.BytesIO(data)))
    assert len(recs) == 2
    assert recs[0][0].startswith(b">one")
    assert recs[1][0].startswith(b">two")

def test_reverse_complement_small_known():
    header = b">x\n"
    seq_str = "ACGT"
    seq = bytearray((seq_str + "\n").encode("ascii"))
    h, out = rc.reverse_complement(header, seq)
    assert h == header
    assert flatten(bytes(out)) == revcomp_naive(seq_str).encode("ascii")
    assert bytes(out).endswith(b"\n")

def test_reverse_complement_iupac_mapping():
    s = "ABCDGHKMNRSTUVWY"
    header = b">iupac\n"
    seq = bytearray((s + "\n").encode("ascii"))
    h, out = rc.reverse_complement(header, seq)
    assert flatten(bytes(out)) == revcomp_naive(s).encode("ascii")
    assert bytes(out).endswith(b"\n")

def test_reverse_complement_wraps_60():
    s = "A"*61
    header = b">wrap\n"
    seq = bytearray((s + "\n").encode("ascii"))
    h, out = rc.reverse_complement(header, seq)
    assert flatten(bytes(out)) == (b"T"*61)
    lines = bytes(out).splitlines()
    seq_lines = [ln for ln in lines if ln and not ln.startswith(b">")]
    assert all(1 <= len(ln) <= 60 for ln in seq_lines)

def test_end_to_end_single_process_output_is_valid_fasta():
    data = make_fasta([("one","GATTACA"), ("two","ACGT"*20)])
    out = run_single_process_like_main(data)
    out_recs = parse_fasta_bytes(out)
    in_recs = parse_fasta_bytes(data)
    assert len(out_recs) == len(in_recs)
    for (h_in, seq_in), (h_out, seq_out) in zip(in_recs, out_recs):
        assert h_out == h_in
        assert seq_out.decode("ascii") == revcomp_naive(seq_in.decode("ascii"))

def test_long_default():
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")
    bp = DEFAULT_LONG_BP
    seq = ("ACGT"*(bp//4+1))[:bp]
    data = make_fasta([("big", seq)])
    t0 = time.time()
    out = run_single_process_like_main(data)
    dt = time.time() - t0
    recs = parse_fasta_bytes(out)
    assert len(recs) == 1
    assert len(recs[0][1]) == bp
    assert dt < 1800
