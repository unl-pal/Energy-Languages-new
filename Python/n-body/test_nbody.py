import os
import copy
import math
import re
import time
import pytest

# CHANGE this import to match your filename (without .py)
import nbody as nb


# -----------------------------
# Defaults: LONG by default
# Disable with: FAST_TEST=1 pytest -q
# Tune with: LONG_STEPS=500000 (default 500000)
# -----------------------------
FAST_TEST = os.getenv("FAST_TEST", "").strip().lower() in {"1", "true", "yes"}
DEFAULT_LONG_STEPS = int(os.getenv("LONG_STEPS", "5000000"))


# -----------------------------
# Helpers
# -----------------------------
def fresh_system():
    """
    Create a deep-copied bodies dict and derived SYSTEM/PAIRS so tests don't
    interfere with each other (because benchmark mutates lists in-place).
    """
    bodies = copy.deepcopy(nb.BODIES)
    system = list(bodies.values())
    pairs = nb.combinations(system)
    return bodies, system, pairs


def total_momentum(system):
    px = py = pz = 0.0
    for (r, v, m) in system:
        px += v[0] * m
        py += v[1] * m
        pz += v[2] * m
    return px, py, pz


def energy(system, pairs):
    e = 0.0
    for (((x1, y1, z1), v1, m1),
         ((x2, y2, z2), v2, m2)) in pairs:
        dx = x1 - x2
        dy = y1 - y2
        dz = z1 - z2
        e -= (m1 * m2) / math.sqrt(dx*dx + dy*dy + dz*dz)
    for (r, (vx, vy, vz), m) in [(b[0], b[1], b[2]) for b in system]:
        e += m * (vx*vx + vy*vy + vz*vz) / 2.0
    return e


def run_offset_momentum(bodies, system):
    # match benchmark API: offset_momentum(ref, bodies=SYSTEM, ...)
    nb.offset_momentum(bodies["sun"], bodies=system)


def run_advance(system, pairs, steps, dt=0.01):
    nb.advance(dt, steps, bodies=system, pairs=pairs)


# -----------------------------
# Unit tests
# -----------------------------
def test_combinations_pair_count():
    # For 5 bodies, should be 10 unordered pairs
    bodies, system, pairs = fresh_system()
    assert len(system) == 5
    assert len(pairs) == 10


def test_offset_momentum_zeroes_total_momentum():
    bodies, system, pairs = fresh_system()
    run_offset_momentum(bodies, system)
    px, py, pz = total_momentum(system)
    assert abs(px) < 1e-9
    assert abs(py) < 1e-9
    assert abs(pz) < 1e-9


def test_energy_finite_and_changes_after_advance():
    bodies, system, pairs = fresh_system()
    run_offset_momentum(bodies, system)
    e0 = energy(system, pairs)
    run_advance(system, pairs, steps=100, dt=0.01)
    e1 = energy(system, pairs)
    assert math.isfinite(e0)
    assert math.isfinite(e1)
    # should generally change (integration step)
    assert e0 != e1


def test_advance_does_not_change_number_of_bodies():
    bodies, system, pairs = fresh_system()
    run_offset_momentum(bodies, system)
    run_advance(system, pairs, steps=10, dt=0.01)
    assert len(system) == 5
    assert len(pairs) == 10


# -----------------------------
# main() output test (small)
# -----------------------------
def test_main_prints_two_lines(monkeypatch, capsys):
    # main() mutates global SYSTEM, so run it in isolation by rebuilding module state:
    # easiest: call functions on a fresh system instead of nb.main().
    bodies, system, pairs = fresh_system()
    nb.offset_momentum(bodies["sun"], bodies=system)
    # capture report_energy prints
    nb.report_energy(bodies=system, pairs=pairs)
    nb.advance(0.01, 10, bodies=system, pairs=pairs)
    nb.report_energy(bodies=system, pairs=pairs)

    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 2
    assert re.match(r"^-?\d+\.\d{9}$", out[0])
    assert re.match(r"^-?\d+\.\d{9}$", out[1])


# -----------------------------
# Long test (DEFAULT ON)
# -----------------------------
def test_long_run_default():
    """
    Default-on longer run to make `pytest -q` take longer.
    Disable with FAST_TEST=1.
    """
    if FAST_TEST:
        pytest.skip("FAST_TEST=1 set; skipping long test")

    bodies, system, pairs = fresh_system()
    nb.offset_momentum(bodies["sun"], bodies=system)

    t0 = time.time()
    nb.advance(0.01, DEFAULT_LONG_STEPS, bodies=system, pairs=pairs)
    dt = time.time() - t0

    e = energy(system, pairs)
    assert math.isfinite(e)

    # very loose bound for shared machines
    assert dt < 1800
