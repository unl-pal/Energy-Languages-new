import os
import re
import time
import pytest
import binarytrees as bt


# -----------------------------
# Defaults (long by default)
# -----------------------------
DEFAULT_LONG_DEPTH = int(os.getenv("LONG_DEPTH", "22"))
DEFAULT_LONG_N = int(os.getenv("LONG_N", "20"))

# If you ever want quick runs:
#   FAST_TEST=1 pytest -q
FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1", "true", "yes"}


# -----------------------------
# Helpers
# -----------------------------
def expected_nodes(depth: int) -> int:
    return (2 ** (depth + 1)) - 1


def parse_main_lines(output: str):
    return [line.strip() for line in output.splitlines() if line.strip()]


# -----------------------------
# Fast correctness tests
# -----------------------------
@pytest.mark.parametrize("d", [0, 1, 2, 3, 4, 7, 10])
def test_check_tree_matches_closed_form(d):
    t = bt.make_tree(d)
    assert bt.check_tree(t) == expected_nodes(d)


def test_leaf_is_one():
    assert bt.check_tree((None, None)) == 1


@pytest.mark.parametrize(
    "i,d,chunksize",
    [
        (0, 4, 2),
        (1, 4, 2),
        (2, 4, 2),
        (3, 4, 2),
        (8, 4, 4),
        (9, 6, 6),
        (5001, 3, 5000),
    ],
)
def test_get_argchunks_content_and_order(i, d, chunksize):
    chunks = list(bt.get_argchunks(i, d, chunksize=chunksize))
    flat = [pair for chunk in chunks for pair in chunk]
    assert flat == [(k, d) for k in range(1, i + 1)]


def test_get_argchunks_requires_even_chunksize():
    with pytest.raises(AssertionError):
        list(bt.get_argchunks(10, 4, chunksize=3)


        )


def test_main_output_deterministic_single_process(capsys, monkeypatch):
    # avoid multiprocessing in normal tests
    monkeypatch.setattr(bt.mp, "cpu_count", lambda: 1)

    n = 4
    bt.main(n)

    out = capsys.readouterr().out
    lines = parse_main_lines(out)

    min_depth = 4
    max_depth = max(min_depth + 2, n)  # 6
    stretch_depth = max_depth + 1      # 7

    assert lines[0].startswith(f"stretch tree of depth {stretch_depth}\t check: ")
    assert lines[0].endswith(str(expected_nodes(stretch_depth)))

    mids = lines[1:-1]
    assert len(mids) == 2
    for line in mids:
        m = re.match(r"(\d+)\t trees of depth (\d+)\t check: (\d+)$", line)
        assert m, f"unexpected line format: {line}"
        i = int(m.group(1))
        d = int(m.group(2))
        cs = int(m.group(3))

        mmd = max_depth + min_depth  # 10
        exp_i = 2 ** (mmd - d)
        exp_cs = exp_i * expected_nodes(d)
        assert i == exp_i
        assert cs == exp_cs

    assert lines[-1].startswith(f"long lived tree of depth {max_depth}\t check: ")
    assert lines[-1].endswith(str(expected_nodes(max_depth)))


# -----------------------------
# Long / deeper tests (DEFAULT ON)
# Disable with: FAST_TEST=1
# Tune with: LONG_DEPTH=..., LONG_N=...
# -----------------------------
def test_deeper_tree_default_on():
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")
    depth = DEFAULT_LONG_DEPTH

    t0 = time.time()
    t = bt.make_tree(depth)
    c = bt.check_tree(t)
    dt = time.time() - t0

    assert c == expected_nodes(depth)
    # Very loose bound to avoid flaky failures; adjust if needed
    assert dt < 180


def test_main_larger_n_default_on(capsys, monkeypatch):
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    # still force single-process for determinism + avoid spawning in tests
    monkeypatch.setattr(bt.mp, "cpu_count", lambda: 1)

    n = DEFAULT_LONG_N
    bt.main(n)

    out = capsys.readouterr().out
    lines = parse_main_lines(out)
    assert lines and "stretch tree" in lines[0] and "long lived tree" in lines[-1]
