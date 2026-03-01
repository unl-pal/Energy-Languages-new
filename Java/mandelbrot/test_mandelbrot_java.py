import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "mandelbrot"

# Heavier default => longer runtime
DEFAULT_N = int(os.getenv("LONG_N", "1200000"))


def run_java(n: int) -> bytes:
    p = subprocess.run(
        ["java", "-cp", str(HERE), CLASS, str(n)],
        cwd=str(HERE),
        capture_output=True,
    )
    assert p.returncode == 0, f"java failed\nSTDERR:\n{p.stderr.decode(errors='replace')}"
    return p.stdout


def expected_size(n: int) -> int:
    header = f"P4\n{n} {n}\n".encode()
    row_bytes = (n + 7) // 8
    return len(header) + n * row_bytes


def test_mandelbrot_end_to_end():
    n = DEFAULT_N
    out = run_java(n)

    header = f"P4\n{n} {n}\n".encode()
    assert out.startswith(header)

    body = out[len(header):]
    assert len(out) == expected_size(n)
    assert len(body) == n * ((n + 7) // 8)


def test_mandelbrot_deterministic():
    n = min(DEFAULT_N, 512)  # keep second run a bit lighter
    out1 = run_java(n)
    out2 = run_java(n)
    assert out1 == out2
