import os
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "knucleotide"
FASTUTIL_JAR = os.getenv("FASTUTIL_JAR", "/usr/share/java/fastutil.jar")
CP = f"{HERE}:{FASTUTIL_JAR}"

REQUESTED_REPEATS = int(os.getenv("LONG_REPEATS", "100000"))
ROUNDS = int(os.getenv("LONG_ROUNDS", "3"))

# Java code crashes past this fixed internal buffer size; stay safely below it.
MAX_INPUT_BYTES = 2_000_000

QUERIES = [
    "GGT",
    "GGTA",
    "GGTATT",
    "GGTATTTTAATT",
    "GGTATTTTAATTTATAGT",
]

ALL_MONO = {"A", "C", "G", "T"}
ALL_DI = {a + b for a in "ACGT" for b in "ACGT"}
PATTERN = "GGTATTTTAATTTATAGT"


def make_input(requested_repeats: int) -> tuple[str, str]:
    header = ">ONE\nAAAA\n>THREE\n"
    footer = "\n>FOUR\nCCCC\n"

    # Compute max repeats that fit under MAX_INPUT_BYTES without ever building a huge string.
    fixed_bytes = len((header + footer).encode("ascii"))
    pattern_bytes = len(PATTERN.encode("ascii"))

    max_safe_repeats = (MAX_INPUT_BYTES - fixed_bytes) // pattern_bytes
    repeats = min(requested_repeats, max_safe_repeats)

    assert repeats > 0, "Computed non-positive safe repeat count"

    seq = PATTERN * repeats
    fasta = f"{header}{seq}{footer}"
    return fasta, seq

def run_java(input_text: str) -> str:
    p = subprocess.run(
        ["java", "-cp", CP, CLASS, "0"],
        cwd=str(HERE),
        text=True,
        input=input_text,
        capture_output=True,
    )
    assert p.returncode == 0, (
        f"java failed\n"
        f"CP={CP}\n"
        f"STDERR:\n{p.stderr}\n"
        f"STDOUT:\n{p.stdout}"
    )
    return p.stdout


def count_overlapping(seq: str, sub: str) -> int:
    c = 0
    start = 0
    while True:
        i = seq.find(sub, start)
        if i == -1:
            return c
        c += 1
        start = i + 1


def parse_blocks(out: str):
    lines = out.splitlines()
    blocks = []
    cur = []
    for line in lines:
        if line.strip() == "":
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line)
    if cur:
        blocks.append(cur)
    return blocks


def validate_output(out: str, seq: str):
    blocks = parse_blocks(out)
    assert len(blocks) == 3, f"unexpected output blocks:\n{out}"

    mono = blocks[0]
    di = blocks[1]
    counts = blocks[2]

    # Zero-frequency entries may be omitted.
    assert 1 <= len(mono) <= 4
    assert 1 <= len(di) <= 16
    assert len(counts) == 5

    mono_seen = set()
    mono_sum = 0.0
    for line in mono:
        m = re.fullmatch(r"([ACGT]) ([0-9]+\.[0-9]{3})", line)
        assert m, f"bad mono line: {line!r}"
        mono_seen.add(m.group(1))
        mono_sum += float(m.group(2))
    assert mono_seen <= ALL_MONO
    assert abs(mono_sum - 100.0) < 0.02

    di_seen = set()
    di_sum = 0.0
    for line in di:
        m = re.fullmatch(r"([ACGT]{2}) ([0-9]+\.[0-9]{3})", line)
        assert m, f"bad di line: {line!r}"
        di_seen.add(m.group(1))
        di_sum += float(m.group(2))
    assert di_seen <= ALL_DI
    assert abs(di_sum - 100.0) < 0.05

    expected = {q: count_overlapping(seq, q) for q in QUERIES}
    for line, q in zip(counts, QUERIES):
        m = re.fullmatch(r"([0-9]+)\t([A-Z]+)", line)
        assert m, f"bad count line: {line!r}"
        assert m.group(2) == q
        assert int(m.group(1)) == expected[q]


def test_knucleotide_end_to_end():
    input_text, seq = make_input(REQUESTED_REPEATS)

    out = None
    for _ in range(ROUNDS):
        out = run_java(input_text)

    validate_output(out, seq)
