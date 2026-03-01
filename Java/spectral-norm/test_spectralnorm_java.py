import math
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "spectralnorm"

N = int(os.getenv("SPECTRAL_N", "200000"))
TOL = float(os.getenv("SPECTRAL_TOL", "5e-9"))


def eval_a(i: int, j: int) -> float:
    return 1.0 / ((((i + j) * (i + j + 1)) >> 1) + i + 1)


def multiply_av(v: list[float]) -> list[float]:
    n = len(v)
    out = [0.0] * n
    for i in range(n):
        s = 0.0
        for j in range(n):
            s += eval_a(i, j) * v[j]
        out[i] = s
    return out


def multiply_atv(v: list[float]) -> list[float]:
    n = len(v)
    out = [0.0] * n
    for i in range(n):
        s = 0.0
        for j in range(n):
            s += eval_a(j, i) * v[j]
        out[i] = s
    return out


def multiply_atav(v: list[float]) -> list[float]:
    return multiply_atv(multiply_av(v))


def reference_spectralnorm(n: int) -> float:
    u = [1.0] * n
    for _ in range(10):
        v = multiply_atav(u)
        u = multiply_atav(v)
    vbv = sum(ue * ve for ue, ve in zip(u, v))
    vv = sum(ve * ve for ve in v)
    return math.sqrt(vbv / vv)


def run_java(n: int) -> str:
    p = subprocess.run(
        ["java", "-cp", str(HERE), CLASS, str(n)],
        cwd=str(HERE),
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0, f"java failed\nSTDERR:\n{p.stderr}\nSTDOUT:\n{p.stdout}"
    return p.stdout.strip()


def test_spectralnorm_end_to_end():
    out = run_java(N)
    got = float(out)
    expected = reference_spectralnorm(N)

    assert abs(got - expected) <= TOL, (
        f"n={N} got {got:.12f} expected {expected:.12f} diff={abs(got - expected):.12e}"
    )

