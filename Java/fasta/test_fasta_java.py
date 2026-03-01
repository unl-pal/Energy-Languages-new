import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "fasta"

IUB = set("acgtBDHKMNRSVWY")
HOMO = set("acgt")
ALU = set("ACGT")

# This implementation needs sufficiently large n.
# Bigger default => longer test runtime.
DEFAULT_N = int(os.getenv("LONG_N", "300000"))


def run_java(n: int) -> str:
    p = subprocess.run(
        ["java", "-cp", str(HERE), CLASS, str(n)],
        cwd=str(HERE),
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0, f"java failed\nSTDERR:\n{p.stderr}\nSTDOUT:\n{p.stdout}"
    return p.stdout


def parse_sections(out: str):
    sections = []
    header = None
    seq_parts = []
    for line in out.splitlines():
        if line.startswith(">"):
            if header is not None:
                sections.append((header, "".join(seq_parts)))
            header = line
            seq_parts = []
        else:
            seq_parts.append(line.strip())
    if header is not None:
        sections.append((header, "".join(seq_parts)))
    return sections


def test_fasta_end_to_end_longer():
    n = DEFAULT_N
    out = run_java(n)
    sections = parse_sections(out)

    assert len(sections) == 3
    assert sections[0][0] == ">ONE Homo sapiens alu"
    assert sections[1][0] == ">TWO IUB ambiguity codes"
    assert sections[2][0] == ">THREE Homo sapiens frequency"

    # Exact lengths
    assert len(sections[0][1]) == 2 * n
    assert len(sections[1][1]) == 3 * n
    assert len(sections[2][1]) == 5 * n

    # Alphabets
    assert set(sections[0][1]) <= ALU
    assert set(sections[1][1]) <= IUB
    assert set(sections[2][1]) <= HOMO

    # Wrapping: all lines should be <= 60 chars, all non-final lines in a block exactly 60
    lines = out.splitlines()
    current_seq_lines = []
    for line in lines:
        if line.startswith(">"):
            if current_seq_lines:
                for seq_line in current_seq_lines[:-1]:
                    assert len(seq_line) == 60
                assert 1 <= len(current_seq_lines[-1]) <= 60
            current_seq_lines = []
        else:
            current_seq_lines.append(line)

    if current_seq_lines:
        for seq_line in current_seq_lines[:-1]:
            assert len(seq_line) == 60
        assert 1 <= len(current_seq_lines[-1]) <= 60
