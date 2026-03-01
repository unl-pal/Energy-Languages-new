import os
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "pidigits"
DEFAULT_N = int(os.getenv("LONG_N", "4000"))


def run_java(n: int) -> str:
    java_opts = os.getenv("JAVA_OPTS", "").split()
    env = os.environ.copy()

    cmd = ["java", *java_opts, "-cp", str(HERE), CLASS, str(n)]
    p = subprocess.run(
        cmd,
        cwd=str(HERE),
        text=True,
        capture_output=True,
        env=env,
    )
    assert p.returncode == 0, (
        f"java failed\nCMD: {' '.join(cmd)}\nSTDERR:\n{p.stderr}\nSTDOUT:\n{p.stdout}"
    )
    return p.stdout


def parse_lines(out: str):
    return [ln for ln in out.splitlines() if ln.strip()]


def extract_pi_digits(out: str) -> str:
    """
    Extract only the printed pi digits, excluding the trailing counters (:10, :20, ...).
    Each line is:
        <10-char block>\t:<count>
    The last block may contain spaces for padding.
    """
    digits = []
    for line in parse_lines(out):
        m = re.fullmatch(r"(.{10})\t:(\d+)", line)
        assert m, f"bad line format: {line!r}"
        block = m.group(1)
        digits.append(block.replace(" ", ""))  # last line may be padded
    return "".join(digits)


def test_known_prefixes():
    known = {
        1:  "3",
        2:  "31",
        5:  "31415",
        10: "3141592653",
        20: "31415926535897932384",
        25: "3141592653589793238462643",
    }
    for n, expected in known.items():
        out = run_java(n)
        d = extract_pi_digits(out)
        assert d[:n] == expected
        assert len(d) == n


def test_line_format():
    n = 25
    out = run_java(n)
    lines = parse_lines(out)

    for i, line in enumerate(lines, 1):
        m = re.fullmatch(r"(.{10})\t:(\d+)", line)
        assert m, f"bad line format: {line!r}"
        block, count = m.group(1), int(m.group(2))
        assert count == min(i * 10, n)

        if count < n:
            assert block.isdigit()
        else:
            assert set(block) <= set("0123456789 ")

    assert len(extract_pi_digits(out)) == n


def test_long_default():
    out = run_java(DEFAULT_N)
    lines = parse_lines(out)

    assert lines
    assert lines[-1].endswith(f"\t:{DEFAULT_N}")
    assert len(extract_pi_digits(out)) == DEFAULT_N
