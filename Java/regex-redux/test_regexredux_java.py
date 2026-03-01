import os
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASS = "regexredux"

REPEATS = int(os.getenv("LONG_REPEATS", "80000"))

VARIANTS = (
    "agggtaaa|tttaccct",
    "[cgt]gggtaaa|tttaccc[acg]",
    "a[act]ggtaaa|tttacc[agt]t",
    "ag[act]gtaaa|tttac[agt]ct",
    "agg[act]taaa|ttta[agt]cct",
    "aggg[acg]aaa|ttt[cgt]ccct",
    "agggt[cgt]aa|tt[acg]accct",
    "agggta[cgt]a|t[acg]taccct",
    "agggtaa[cgt]|[acg]ttaccct",
)

SUBST = {
    "tHa[Nt]": "<4>",
    "aND|caN|Ha[DS]|WaS": "<3>",
    "a[NSt]|BY": "<2>",
    "<[^>]*>": "|",
    "\\|[^|][^|]*\\|": "-",
}


def make_input(repeats: int) -> tuple[str, str]:
    # Lowercase sequence to match the benchmark regexes.
    seq = ("agggtaaa" * repeats).lower()

    # Wrap at 60 chars like FASTA input commonly does.
    wrapped = "\n".join(seq[i:i+60] for i in range(0, len(seq), 60))
    raw = f">THREE\n{wrapped}\n"
    return raw, seq


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


def strip_fasta(raw: str) -> str:
    return re.sub(">.*\n|\n", "", raw)


def reference_counts(clean_seq: str):
    return [len(re.findall(pat, clean_seq)) for pat in VARIANTS]


def reference_subst(clean_seq: str) -> str:
    s = clean_seq
    for f, r in SUBST.items():
        s = re.sub(f, r, s)
    return s


def test_regexredux_end_to_end():
    raw, _ = make_input(REPEATS)
    out = run_java(raw)

    clean = strip_fasta(raw)
    ref_counts = reference_counts(clean)
    ref_subst = reference_subst(clean)

    lines = out.splitlines()

    # First 9 lines: "<pattern> <count>"
    first9 = lines[:9]
    assert len(first9) == 9
    for i, line in enumerate(first9):
        pat, count = line.rsplit(" ", 1)
        assert pat == VARIANTS[i]
        assert int(count) == ref_counts[i]

    # Last 3 non-empty lines are lengths
    tail = [ln.strip() for ln in lines if ln.strip()][-3:]
    ilen = int(tail[0])
    clen = int(tail[1])
    rlen = int(tail[2])

    assert ilen == len(raw)
    assert clen == len(clean)
    assert rlen == len(ref_subst)
