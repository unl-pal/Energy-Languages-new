import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "revcomp"

RECORDS = int(os.getenv("REVCOMP_RECORDS", "3"))
LINES_PER_RECORD = int(os.getenv("REVCOMP_LINES", "400000"))
WIDTH = int(os.getenv("REVCOMP_WIDTH", "60"))

COMP = {chr(i): chr(i) for i in range(256)}
COMP.update({
    "t": "A", "T": "A",
    "a": "T", "A": "T",
    "g": "C", "G": "C",
    "c": "G", "C": "G",
    "v": "B", "V": "B",
    "h": "D", "H": "D",
    "r": "Y", "R": "Y",
    "m": "K", "M": "K",
    "y": "R", "Y": "R",
    "k": "M", "K": "M",
    "b": "V", "B": "V",
    "d": "H", "D": "H",
    "u": "A", "U": "A",
})

# Include all mapped bases plus a few intentionally unmapped characters that should pass through.
SEEDS = [
    "ACGTBDHKMRVYUacgtbdhkmrvyunN",
    "TTGCAAGGCCBDHKMRVYUttgcaa--nn",
    "GATTACAVHDBMKRYUcgtaXYZnnuu",
]


def run_java(input_text: str) -> str:
    p = subprocess.run(
        ["java", "-cp", str(HERE), CLASS, "0"],
        cwd=str(HERE),
        text=True,
        input=input_text,
        capture_output=True,
    )
    assert p.returncode == 0, f"java failed\nSTDERR:\n{p.stderr}\nSTDOUT:\n{p.stdout}"
    return p.stdout



def parse_fasta(raw: str):
    records = []
    header = None
    seq_lines = []

    for line in raw.splitlines():
        if line.startswith(">"):
            if header is not None:
                records.append((header, seq_lines))
            header = line
            seq_lines = []
        else:
            seq_lines.append(line)

    if header is not None:
        records.append((header, seq_lines))

    return records



def reference_revcomp(raw: str) -> str:
    parts = []

    for header, seq_lines in parse_fasta(raw):
        seq = "".join(seq_lines)
        widths = [len(line) for line in seq_lines]
        rev = "".join(COMP[ch] for ch in reversed(seq))

        parts.append(header)
        pos = 0
        for width in widths:
            parts.append(rev[pos : pos + width])
            pos += width

    return "\n".join(parts) + "\n"



def make_input(records: int, lines_per_record: int, width: int) -> str:
    parts = []
    for i in range(records):
        seed = SEEDS[i % len(SEEDS)]
        repeated = (seed * ((lines_per_record * width // len(seed)) + 2))[: lines_per_record * width]
        parts.append(f">SEQ{i + 1}")
        for j in range(0, len(repeated), width):
            parts.append(repeated[j : j + width])
    return "\n".join(parts) + "\n"



def test_revcomp_end_to_end_long():
    raw = make_input(RECORDS, LINES_PER_RECORD, WIDTH)

    out = run_java(raw)
    expected = reference_revcomp(raw)

    assert out == expected
