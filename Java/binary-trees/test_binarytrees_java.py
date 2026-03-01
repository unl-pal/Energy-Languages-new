import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "binarytrees"

def run(n: int) -> list[str]:
    p = subprocess.run(
        ["java", "-cp", str(HERE), CLASS, str(n)],
        cwd=str(HERE),
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0, f"java failed\nSTDERR:\n{p.stderr}\nSTDOUT:\n{p.stdout}"
    return [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]

def nodes(d: int) -> int:
    return (2 ** (d + 1)) - 1

def test_n4_exact():
    L = run(4)
    assert L[0] == "stretch tree of depth 7\t check: 255"
    assert L[1] == "64\t trees of depth 4\t check: 1984"
    assert L[2] == "16\t trees of depth 6\t check: 2032"
    assert L[-1] == "long lived tree of depth 6\t check: 127"

def test_structure_n21():
    n = 21
    L = run(n)
    min_depth = 4
    max_depth = max(min_depth + 2, n)
    stretch = max_depth + 1

    assert L[0].startswith(f"stretch tree of depth {stretch}\t check: ")
    assert L[0].endswith(str(nodes(stretch)))
    assert L[-1].startswith(f"long lived tree of depth {max_depth}\t check: ")
    assert L[-1].endswith(str(nodes(max_depth)))

    ds = list(range(min_depth, stretch, 2))
    mids = L[1:-1]
    assert len(mids) == len(ds)

    mmd = max_depth + min_depth
    for line, d in zip(mids, ds):
        m = re.match(r"(\d+)\t trees of depth (\d+)\t check: (\d+)$", line)
        assert m
        i = int(m.group(1)); dd = int(m.group(2)); cs = int(m.group(3))
        assert dd == d
        exp_i = 2 ** (mmd - d)
        exp_cs = exp_i * nodes(d)
        assert i == exp_i
        assert cs == exp_cs
