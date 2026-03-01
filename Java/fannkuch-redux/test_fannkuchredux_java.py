import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "fannkuchredux"

def run_java(n: int) -> tuple[int, int, str]:
    p = subprocess.run(
        ["java", "-cp", str(HERE), CLASS, str(n)],
        cwd=str(HERE),
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0, f"java failed\nSTDERR:\n{p.stderr}\nSTDOUT:\n{p.stdout}"
    lines = [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]
    assert len(lines) == 2, f"unexpected output: {p.stdout!r}"
    checksum = int(lines[0])
    prefix = f"Pfannkuchen({n}) = "
    assert lines[1].startswith(prefix), f"unexpected second line: {lines[1]!r}"
    flips = int(lines[1][len(prefix):])
    return checksum, flips, p.stdout

def test_small_known_values():
    # deterministic known values for fannkuch-redux
    known = {
        0: (0, 0),
        1: (0, 0),
        2: (-1, 1),
        3: (2, 2),
        4: (4, 4),
        5: (11, 7),
        6: (49, 10),
        7: (228, 16),
    }
    for n, (exp_chk, exp_flips) in known.items():
        chk, flips, _ = run_java(n)
        assert chk == exp_chk
        assert flips == exp_flips

def test_invalid_range():
    chk, flips, _ = run_java(13)
    assert chk == -1
    assert flips == -1

def test_default_benchmark_case():
    chk, flips, _ = run_java(12)
    # sanity only; exact value is large but deterministic
    assert isinstance(chk, int)
    assert flips > 0
