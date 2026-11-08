"""Own tests. Run from the repository root: python3 tests/student/test_student.py
Optimal values are checked against independent brute-force oracles on small inputs;
non-unique witnesses (LCS string, merge plan, tree set) are checked by validity."""
import json
import pathlib
import random
import subprocess
import sys
from functools import lru_cache

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Python" / "source"))
import algorithms as A  # noqa: E402

passed = failed = 0


def check(name, cond, info=""):
    global passed, failed
    if cond:
        passed += 1
        print("PASS", name)
    else:
        failed += 1
        print("FAIL", name, info)


# ------------------------------------------------------------ oracles / validators
def is_subseq(s, t):
    it = iter(t)
    return all(c in it for c in s)


def brute_lcs(a, b):
    best = 0
    for mask in range(1 << len(a)):
        s = "".join(a[i] for i in range(len(a)) if mask >> i & 1)
        if len(s) > best and is_subseq(s, b):
            best = len(s)
    return best


def lcs_ok(a, b, res, expected):
    s = res["sequence"]
    return res["length"] == len(s) == expected and is_subseq(s, a) and is_subseq(s, b)


def brute_merge(sizes):
    @lru_cache(maxsize=None)
    def f(t):
        if len(t) <= 1:
            return 0
        return min(t[i] + t[i + 1] + f(t[:i] + (t[i] + t[i + 1],) + t[i + 2:])
                   for i in range(len(t) - 1))
    return f(tuple(sizes))


def merge_ok(sizes, res, expected=None):
    n = len(sizes)
    if n <= 1:
        return res["cost"] == 0 and res["plan"] == []
    blocks = {(i, i): sizes[i] for i in range(n)}
    total = 0
    for l, k, r in res["plan"]:
        if (l, k) not in blocks or (k + 1, r) not in blocks:
            return False
        s = blocks.pop((l, k)) + blocks.pop((k + 1, r))
        total += s
        blocks[(l, r)] = s
    ok = len(res["plan"]) == n - 1 and list(blocks) == [(0, n - 1)] and total == res["cost"]
    return ok and (expected is None or res["cost"] == expected)


def brute_tree(n, w, edges):
    best = 0
    for mask in range(1 << n):
        if all(not (mask >> u & 1 and mask >> v & 1) for u, v in edges):
            best = max(best, sum(w[i] for i in range(n) if mask >> i & 1))
    return best


def tree_ok(n, w, edges, res, expected):
    sel = res["selected"]
    s = set(sel)
    return (len(s) == len(sel) and all(0 <= v < n for v in sel)
            and all(not (u in s and v in s) for u, v in edges)
            and sum(w[v] for v in sel) == res["weight"] == expected)


def ref_find(text, pat):
    if not pat:
        return list(range(len(text) + 1))
    return [i for i in range(len(text) - len(pat) + 1) if text.startswith(pat, i)]


def suffix_ok(text, res):
    """Valid suffix array + exact adjacent LCP + repeated string, without building all suffixes."""
    n = len(text)
    sa, lcp, rep = res["sa"], res["lcp"], res["repeated"]
    if sorted(sa) != list(range(n)) or len(lcp) != n:
        return False
    if n == 0:
        return rep == ""
    if lcp[0] != 0:
        return False
    for i in range(1, n):
        x, y, h = sa[i - 1], sa[i], lcp[i]
        if text[x:x + h] != text[y:y + h]:
            return False
        if x + h < n and y + h < n:
            if text[x + h] >= text[y + h]:
                return False  # lcp not maximal, or wrong order
        elif y + h >= n and x + h < n:
            return False  # suffix y is a prefix of x, so y must come first
    best = max(lcp)
    if len(rep) != best:
        return False
    if best == 0:
        return True
    return len(ref_find(text, rep)) >= 2 if n <= 3000 else True


rng = random.Random(2026)

# ------------------------------------------------------------ LCS
check("lcs published example", lcs_ok("tea_time", "team", A.lcs({"a": "tea_time", "b": "team"}), 4))
check("lcs empty a", A.lcs({"a": "", "b": "abc"}) == {"length": 0, "sequence": ""})
check("lcs empty both", A.lcs({"a": "", "b": ""}) == {"length": 0, "sequence": ""})
check("lcs identical", A.lcs({"a": "abc", "b": "abc"})["sequence"] == "abc")
check("lcs disjoint", A.lcs({"a": "aaa", "b": "bbb"})["length"] == 0)
ok = True
for _ in range(300):
    a = "".join(rng.choice("abc") for _ in range(rng.randint(0, 8)))
    b = "".join(rng.choice("abc") for _ in range(rng.randint(0, 9)))
    ok &= lcs_ok(a, b, A.lcs({"a": a, "b": b}), brute_lcs(a, b))
check("lcs 300 random vs brute force", ok)
a = "".join(rng.choice("abc") for _ in range(1000))
b = "".join(c for i, c in enumerate(a) if i % 3)  # b is a subsequence of a => LCS = len(b)
check("lcs 1000x~667 near full limit", lcs_ok(a, b, A.lcs({"a": a, "b": b}), len(b)))
a2 = "".join(rng.choice("ab") for _ in range(1000))
r = A.lcs({"a": a2, "b": a2})
check("lcs 1000x1000 identical (limit 1e6)", r["length"] == 1000 and r["sequence"] == a2)

# ------------------------------------------------------------ merge
check("merge published example", merge_ok([2, 3, 4], A.merge({"sizes": [2, 3, 4]}), 14))
check("merge empty/one", A.merge({"sizes": []}) == {"cost": 0, "plan": []}
      and A.merge({"sizes": [5]}) == {"cost": 0, "plan": []})
check("merge zeros", merge_ok([0, 0, 0], A.merge({"sizes": [0, 0, 0]}), 0))
ok = True
for _ in range(200):
    s = [rng.randint(0, 20) for _ in range(rng.randint(0, 7))]
    ok &= merge_ok(s, A.merge({"sizes": s}), brute_merge(s))
check("merge 200 random vs brute force", ok)
big = [10**9] * 200
r = A.merge({"sizes": big})
check("merge n=200, sizes 1e9 (valid plan, 64-bit)", merge_ok(big, r) and r["cost"] > 2**31)
check("merge validator rejects non-adjacent plan",
      not merge_ok([1, 1, 1], {"cost": 4, "plan": [[0, 0, 2], [0, 1, 2]]}))

# ------------------------------------------------------------ tree
check("tree published example", tree_ok(3, [4, 9, 6], [[0, 1], [1, 2]],
      A.tree({"n": 3, "weights": [4, 9, 6], "edges": [[0, 1], [1, 2]]}), 10))
check("tree empty", A.tree({"n": 0, "weights": [], "edges": []}) == {"weight": 0, "selected": []})
check("tree single positive", tree_ok(1, [5], [], A.tree({"n": 1, "weights": [5], "edges": []}), 5))
check("tree all negative -> empty set", A.tree({"n": 2, "weights": [-1, -2], "edges": [[0, 1]]})["weight"] == 0)
ok = True
for _ in range(300):
    n = rng.randint(1, 12)
    w = [rng.randint(-5, 10) for _ in range(n)]
    e = [[rng.randrange(i), i] for i in range(1, n)]
    ok &= tree_ok(n, w, e, A.tree({"n": n, "weights": w, "edges": e}), brute_tree(n, w, e))
check("tree 300 random trees vs brute force", ok)
n = 100000
chain = [[i, i + 1] for i in range(n - 1)]
check("tree deep chain n=100000 (all 1 -> 50000)",
      tree_ok(n, [1] * n, chain, A.tree({"n": n, "weights": [1] * n, "edges": chain}), 50000))
star = [[0, i] for i in range(1, n)]
w = [10] + [1] * (n - 1)
check("tree star n=100000 (leaves win)", tree_ok(n, w, star, A.tree({"n": n, "weights": w, "edges": star}), n - 1))
wn = [-10**9] * n
check("tree chain all -1e9 -> 0", A.tree({"n": n, "weights": wn, "edges": chain}) == {"weight": 0, "selected": []})

# ------------------------------------------------------------ naive / kmp / rk
for name, f in (("naive", A.naive), ("kmp", A.kmp), ("rk", A.rk)):
    check(name + " overlaps", f({"text": "aaaaa", "pattern": "aaa"})["positions"] == [0, 1, 2])
    check(name + " empty pattern", f({"text": "abc", "pattern": ""})["positions"] == [0, 1, 2, 3])
    check(name + " both empty", f({"text": "", "pattern": ""})["positions"] == [0])
    check(name + " pattern longer", f({"text": "ab", "pattern": "abc"})["positions"] == [])
    check(name + " case and spaces", f({"text": "Ab ab AB", "pattern": "ab"})["positions"] == [3])
    ok = True
    for _ in range(300):
        t = "".join(rng.choice("ab") for _ in range(rng.randint(0, 30)))
        p = "".join(rng.choice("ab") for _ in range(rng.randint(0, 5)))
        ok &= f({"text": t, "pattern": p})["positions"] == ref_find(t, p)
    check(name + " 300 random vs reference", ok)
check("rk collision ab/dj (hash 75), only ab", A.rk({"text": "abdj", "pattern": "ab"})["positions"] == [0])
check("rk many collisions still exact", A.rk({"text": "abdjabdj", "pattern": "dj"})["positions"] == [2, 6])
t = "a" * 200000
r = A.kmp({"text": t, "pattern": "a" * 100000})["positions"]
check("kmp full limit all-a (100001 starts)", len(r) == 100001 and r[0] == 0 and r[-1] == 100000)
t = "".join(rng.choice("ab") for _ in range(200000))
p = "abbab"
check("kmp 200000 random vs reference", A.kmp({"text": t, "pattern": p})["positions"] == ref_find(t, p))
t = "".join(rng.choice("ab") for _ in range(3000))
p = "".join(rng.choice("ab") for _ in range(1000))
check("naive == kmp == rk at 3000", A.naive({"text": t, "pattern": p}) == A.kmp({"text": t, "pattern": p})
      == A.rk({"text": t, "pattern": p}))
t, p = "a" * 5000, "a" * 4000
check("rk |text|*|pattern|=2e7 matches kmp", A.rk({"text": t, "pattern": p}) == A.kmp({"text": t, "pattern": p}))

# ------------------------------------------------------------ suffix
check("suffix banana", suffix_ok("banana", A.suffix({"text": "banana"}))
      and A.suffix({"text": "banana"})["sa"] == [5, 3, 1, 0, 4, 2])
check("suffix empty", A.suffix({"text": ""}) == {"sa": [], "lcp": [], "repeated": ""})
check("suffix one char", A.suffix({"text": "a"}) == {"sa": [0], "lcp": [0], "repeated": ""})
check("suffix no repeat", A.suffix({"text": "abc"})["repeated"] == "")
ok = True
for _ in range(300):
    t = "".join(rng.choice("ab") for _ in range(rng.randint(0, 25)))
    r = A.suffix({"text": t})
    ok &= suffix_ok(t, r) and r["sa"] == sorted(range(len(t)), key=lambda i: t[i:])
check("suffix 300 random vs sorted-suffix oracle", ok)
t = "a" * 50000
r = A.suffix({"text": t})
check("suffix n=50000 all-a", r["sa"] == list(range(49999, -1, -1)) and r["lcp"][-1] == 49999 and suffix_ok(t, r))
t = "".join(rng.choice("ab") for _ in range(50000))
check("suffix n=50000 random valid", suffix_ok(t, A.suffix({"text": t})))
t = "ab" * 25000
check("suffix n=50000 periodic valid", suffix_ok(t, A.suffix({"text": t})))

# ------------------------------------------------------------ Aho-Corasick
r = A.aho({"patterns": ["he", "she", "he"], "texts": ["sheshe", "sheshe", ""]})
check("aho published example", r["counts"] == [[2, 2, 2], [2, 2, 2], [0, 0, 0]])
check("aho empty dictionary", A.aho({"patterns": [], "texts": ["a", ""]})["counts"] == [[], []])
check("aho no texts", A.aho({"patterns": ["a"], "texts": []})["counts"] == [])
check("aho overlaps", A.aho({"patterns": ["aa"], "texts": ["aaaa"]})["counts"] == [[3]])
ok = True
for _ in range(200):
    pats = ["".join(rng.choice("ab") for _ in range(rng.randint(1, 4))) for _ in range(rng.randint(0, 6))]
    txs = ["".join(rng.choice("ab") for _ in range(rng.randint(0, 20))) for _ in range(rng.randint(0, 4))]
    want = [[len(ref_find(t, p)) for p in pats] for t in txs]
    ok &= A.aho({"patterns": pats, "texts": txs})["counts"] == want
check("aho 200 random vs reference", ok)
pats = ["a" * k for k in range(1, 401)]  # total length 80200
txs = ["a" * 2000 for _ in range(100)]    # total length 200000
r = A.aho({"patterns": pats, "texts": txs})["counts"]
check("aho dense full limit", all(row == [2000 - k + 1 for k in range(1, 401)] for row in r))

# ------------------------------------------------------------ repeated mixed requests via main.py
reqs = [
    {"task": "ping"},
    {"task": "lcs", "a": "tea_time", "b": "team"},
    {"task": "merge", "sizes": [2, 3, 4]},
    {"task": "tree", "n": 3, "weights": [4, 9, 6], "edges": [[0, 1], [1, 2]]},
    {"task": "naive", "text": "aaaaa", "pattern": "aaa"},
    {"task": "kmp", "text": "abababa", "pattern": "aba"},
    {"task": "rk", "text": "abdj", "pattern": "ab"},
    {"task": "suffix", "text": "banana"},
    {"task": "aho", "patterns": ["he", "she", "he"], "texts": ["sheshe", "sheshe", ""]},
]
lines = [json.dumps(q) for q in reqs] * 2
(ROOT / "tests" / "student" / "cases.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
out = subprocess.run([sys.executable, str(ROOT / "Python" / "source" / "main.py")],
                     input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8")
got = [json.loads(x) for x in out.stdout.splitlines()]
k = len(reqs)
check("main.py: one result line per request", len(got) == 2 * k, out.stderr)
check("main.py: state reset (second batch == first)", got[:k] == got[k:])
check("main.py: mixed results correct",
      got[1]["length"] == 4 and got[2]["cost"] == 14 and got[3]["weight"] == 10
      and got[4]["positions"] == [0, 1, 2] and got[7]["sa"] == [5, 3, 1, 0, 4, 2])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
