"""naive vs KMP vs exact Rabin-Karp benchmark. Run from the repository root:
python3 tests/student/benchmark.py"""
import gc
import pathlib
import platform
import random
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Python" / "source"))
import algorithms as A  # noqa: E402

SEED, RUNS, WARMUP = 2026, 5, 1
SIZES = [(1000, 100), (2000, 200), (3000, 300)]  # (|text|, |pattern|) valid for all three methods
METHODS = [("naive", A.naive), ("kmp", A.kmp), ("rk", A.rk)]


def measure(f, req):
    for _ in range(WARMUP):
        f(req)
    ts = []
    for _ in range(RUNS):
        gc.collect()
        t0 = time.perf_counter()
        res = f(req)
        ts.append(time.perf_counter() - t0)
    return ts, res["positions"]


print("Environment:", platform.platform(), "|", platform.machine())
print("Python:", sys.version.split()[0], "| Timer: time.perf_counter")
print(f"Seed: {SEED} | warm-up: {WARMUP} | timed runs: {RUNS}")
print("Timing boundary: only the algorithm call f(request); input generation excluded.\n")

rng = random.Random(SEED)
tables = {}
for family in ("random", "adversarial"):
    rows = []
    for n, m in SIZES:
        if family == "random":
            text = "".join(rng.choice("abcd") for _ in range(n))
            pat = "".join(rng.choice("abcd") for _ in range(m))
        else:  # naive worst case: long near-matches everywhere
            text = "a" * n
            pat = "a" * (m - 1) + "b"
        req = {"text": text, "pattern": pat}
        row, ref = [n, m], None
        for name, f in METHODS:
            ts, pos = measure(f, req)
            assert ref is None or pos == ref, "methods disagree"
            ref = pos
            row.append(ts)
            print(f"{family} n={n} m={m} {name:5s} runs:", [round(t, 5) for t in ts],
                  "median:", round(statistics.median(ts), 5))
        rows.append(row)
    tables[family] = rows

for family, rows in tables.items():
    print(f"\nInput family: {family}")
    print("| text n | pattern m | naive median (s) | KMP median (s) | RK median (s) |")
    print("|---|---|---|---|---|")
    for n, m, a, b, c in rows:
        print(f"| {n} | {m} | {statistics.median(a):.5f} | {statistics.median(b):.5f} | {statistics.median(c):.5f} |")
