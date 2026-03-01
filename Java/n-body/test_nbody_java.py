import os
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "nbody"

DEFAULT_N = int(os.getenv("LONG_N", "500000"))


def run_java(n: int) -> list[str]:
    p = subprocess.run(
        ["java", "-cp", str(HERE), CLASS, str(n)],
        cwd=str(HERE),
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0, f"java failed\nSTDERR:\n{p.stderr}\nSTDOUT:\n{p.stdout}"
    return [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]


def test_small_known_output():
    # For n=0, benchmark should print the same energy twice.
    lines = run_java(0)
    assert len(lines) == 2
    assert lines[0] == "-0.169075164"
    assert lines[1] == "-0.169075164"


def test_output_format_and_stability():
    lines = run_java(DEFAULT_N)
    assert len(lines) == 2

    for line in lines:
        assert re.fullmatch(r"-?\d+\.\d{9}", line), f"bad line format: {line!r}"

    # Energy should change after advancing for n > 0
    if DEFAULT_N > 0:
        assert lines[0] != lines[1]
