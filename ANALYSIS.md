# Assignment 4: Dynamic Programming and String Processing. Analysis

Language: Python 3.14.0 (requirement: 3.12+). Source: `Python/source/algorithms.py` (eight commands) with the supplied adapter `Python/source/main.py`. No recursion is used anywhere (all traversals use loops and explicit stacks/queues), and no built-in substring search (`find`, `in`, `re`, `startswith`) is used inside the algorithms.

Notation: `n`, `m` are text and pattern lengths (or the number of vertices/blocks, see the part), `z` is the number of reported starts.

## 1. Build, run and test commands

No compilation step (Python). Run everything from the repository root.

```sh
python3 tools/run.py --setup                                                    # startup check
python3 tools/run.py --check                                                    # 44 public cases + state reset
python3 tests/student/test_student.py > tests/student/test_results.txt 2>&1     # own tests (63 checks)
python3 tools/run.py --input tests/student/cases.jsonl > tests/student/cases_actual.txt   # actual outputs of own JSON Lines cases
python3 tests/student/benchmark.py > tests/student/benchmark_results.txt        # naive / KMP / RK benchmark
```

Results of the last runs: `--setup` and `--check` pass (44 public cases and the repeated mixed batch); `test_student.py` reports `63 passed, 0 failed`; `cases_actual.txt` has 18 result lines (9 requests, sent twice in one process).

## 2. Common design notes

**State reset.** Every function reads only its own `request` dict and builds all tables (DP matrices, adjacency lists, tries, rank arrays, hash values) as local variables. There are no module-level mutable variables, so one request cannot influence the next. `main.py` handles each input line independently. The public check "state reset: two complete batches in one process" and the own test "main.py: state reset (second batch == first)" confirm that two identical batches in one process give identical results.

**Deep inputs.** The tree DP processes vertices with an explicit BFS order list instead of recursion, so a chain of 100000 vertices does not hit Python's recursion limit. Merge-plan extraction uses an explicit stack. All other parts are loops.

**Integers.** Python integers are arbitrary precision. Anyway the values fit into signed 64 bits: a merge plan has at most 199 merges and each costs at most the total size 2·10¹¹, so the cost is below 4·10¹³; tree weights are at most 10⁵ · 10⁹ = 10¹⁴ in absolute value.

**Alternative optima.** Where the contract accepts any optimal witness, the code returns the first one found with strict comparisons (ties keep the earlier option). The own tests check optimal values against independent brute-force oracles and check witnesses by validity, not by equality.

## 3. Parts

### 3.1 Part 1: LCS (`lcs`)

**State.** `dp[i][j]` is the length of the longest common subsequence of the prefixes `a[:i]` and `b[:j]`. Base cases: `dp[0][j] = dp[i][0] = 0` (an empty prefix shares nothing).

**Transition.** If `a[i-1] == b[j-1]`, then `dp[i][j] = dp[i-1][j-1] + 1`. Otherwise `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.

**Correctness.** If the last characters match, some optimal subsequence of the two prefixes can use them as its last pair (exchange argument: any optimal solution that does not match them can be changed to do so without loss), so the answer is the optimum of the shorter prefixes plus one. If they differ, at least one of them is unused by every common subsequence, so the answer is the better of dropping the last character of `a` or of `b`. The order of shared characters is preserved because only prefixes are extended.

**Reconstruction.** Start at `(n, m)`. If the characters match, emit the character and move to `(i-1, j-1)`. Otherwise move to the neighbour with the larger `dp` value (`dp[i-1][j]` on ties). Emit characters in reverse and reverse the result. Each step keeps the invariant "remaining optimum = `dp[i][j]`", so the emitted string has length `dp[n][m]` and is a subsequence of both inputs (not necessarily contiguous).

**Boundaries.** Either string empty gives `{"length": 0, "sequence": ""}`; identical strings; disjoint alphabets; `|a|·|b| = 10⁶`.

**Complexity.** Time O((n+1)(m+1)); memory O((n+1)(m+1)) for the table (needed for reconstruction) plus O(length) for the output.

### 3.2 Part 2: Ordered block merging (`merge`)

**State.** `dp[l][r]` is the minimum cost of merging original blocks `l..r` into one block while keeping adjacency. `pre` holds prefix sums, so the size of an interval is `pre[r+1] - pre[l]`.

**Transition.** The last merge of interval `[l, r]` joins `[l, k]` and `[k+1, r]` for some `k`. Its cost is the size of the whole interval, so `dp[l][r] = min over k of (dp[l][k] + dp[k+1][r]) + size(l..r)`; `dp[i][i] = 0`. The best `k` is stored in `split[l][r]` (first minimum).

**Correctness.** Every merge order for an interval ends with exactly one last merge of two adjacent sub-intervals, and the two sub-intervals are merged independently, so the optimal cost decomposes (optimal substructure). Merging only adjacent blocks is enforced by using contiguous intervals. A greedy "merge the two smallest blocks" can violate adjacency and is not used.

**Plan.** Walk the split tree from `[0, n-1]` with a stack and append `[l, k, r]` in preorder (parent before children). Reversing this list puts every child merge before its parent merge, which is a valid chronological order using original indices. The plan has exactly `n-1` merges.

**Boundaries.** `n = 0` or `1` returns cost 0 and an empty plan; zero sizes; `n = 200` with sizes `10⁹`.

**Complexity.** O(n³) time, O(n²) auxiliary memory; O(1) for no blocks. No advanced optimization.

### 3.3 Part 3: Tree independent set (`tree`)

**State.** For every vertex `v`: `take[v]` is the best weight in the subtree of `v` if `v` is selected, `skip[v]` if `v` is not selected.

**Transition.** `take[v] = weights[v] + sum of skip[c]` over children, `skip[v] = sum of max(take[c], skip[c])` over children. The answer is `max(take[root], skip[root])`. Because `skip` never goes below 0 (a leaf has `skip = 0`), the empty set is allowed, so an all-negative tree returns weight 0.

**Order.** Compute a BFS order from vertex 0 with a parent array, then process the vertices in reverse BFS order (children before parents). This is the iterative equivalent of postorder.

**Reconstruction.** Go through the vertices in BFS order (parents first). The root is selected iff `take[root] > skip[root]`. A child is forced out if its parent is selected; otherwise it is selected iff `take[c] > skip[c]`. This follows the optimal choice at every vertex and never selects two adjacent vertices. The sum of the selected weights equals the returned `weight`.

**Boundaries.** `n = 0`; `n = 1`; negative weights; chain and star with 100000 vertices; the root choice does not change the optimum (checked against brute force on random trees).

**Complexity.** O(n+1) time and auxiliary memory including reconstruction.

### 3.4 Part 4: Exact search

All three methods share one contract: return all zero-based starts in increasing order including overlaps; an empty pattern returns every boundary `0..n`; a pattern longer than the text returns `[]`.

**Naive (`naive`).** For each start `i` in `0..n-m`, compare characters until the first mismatch or until `m` characters match. Correct because it checks every possible start. Time O((n−m+1)·m) = O(n·m) in the worst case, O(1) auxiliary memory plus the output. The last valid start is `n-m`; the empty pattern outputs `n+1` starts.

**KMP (`kmp`).** `pi[i]` is the length of the longest proper prefix of `pattern[:i+1]` that is also its suffix. After a mismatch at pattern position `k` the matcher falls back to `pi[k-1]` (the longest border that can still match) instead of restarting. After a full match it also falls back to `pi[m-1]`, which keeps overlapping matches (for example `aba` in `abababa` at starts 0, 2, 4). Invariant: after reading `text[i]`, `k` is the length of the longest prefix of the pattern that is a suffix of `text[:i+1]`. Time O(n + m + z), auxiliary memory O(m).

**Rabin–Karp (`rk`).** Polynomial hash with base 31 and modulus 101, ASCII codes, the leftmost character has the highest power: `h = (h·31 + code) mod 101`. Rolling update when moving the window: `h = ((h − code(old)·31^(m−1))·31 + code(new)) mod 101` (Python's `%` keeps the result non-negative, which normalizes negative remainders). Equal hashes are only candidates: every candidate is verified character by character before it is reported, so the small modulus never causes a wrong answer (test: `abdj` with pattern `ab`, both windows hash to 75, only `ab` is reported). Time O(n + m + c·m), where `c` is the number of equal-hash windows; with the tiny modulus this can reach O(n·m), so no linear worst case is claimed. Auxiliary memory O(1) with a rolling window plus the output.

### 3.5 Part 5: Suffix array and Kasai LCP (`suffix`)

**Prefix doubling.** `rank[i]` first holds the character code. In round `k = 1, 2, 4, …` every suffix gets the key `rank[i]·B + (rank[i+k] + 1 if i+k < n else 0)` with `B = max(n, 128) + 2` (the `+1` makes a missing second half smaller than any real rank, so shorter suffixes sort first). The suffix array is sorted by this key and new ranks are assigned: equal keys share a rank. After round `k` the suffixes are ordered by their first `2k` characters. The loop stops when all ranks are distinct, which happens after at most `⌈log₂ n⌉ + 1` rounds. Then `rank` is the inverse of `sa`.

**Kasai.** Process the suffixes in text order, keeping `h` as the current common-prefix length with the previous suffix in `sa` order. When moving from suffix `i` to `i+1`, the LCP can decrease by at most 1, so `h` is decremented by one (if positive) and extended, instead of restarting from 0. Total extensions are bounded by `2n`. `lcp[0] = 0`, `lcp[r]` compares `sa[r-1]` and `sa[r]`.

**Longest repeat.** Two distinct suffixes share a prefix of length `L` exactly when their common prefix length is at least `L`. The maximum common prefix over all pairs of suffixes is attained by an adjacent pair in sorted order, so `max(lcp)` is the length of the longest substring that occurs at two distinct starts (overlaps allowed). The answer is `text[sa[r] : sa[r] + max(lcp)]` for an `r` with `lcp[r] = max(lcp)`; if the maximum is 0 the answer is `""`.

**Boundaries.** Empty text returns empty `sa`, `lcp` and `repeated`; one character; all equal characters (`n = 50000`); periodic text; no sentinel and no empty suffix in the output; suffixes are never materialized as strings.

**Complexity.** Each doubling round sorts with a comparison sort in O(n log n), so prefix doubling costs O(n log² n) time (not the radix-sort O(n log n) variant). Kasai is O(n). Memory is O(n) for the arrays plus the output.

### 3.6 Part 6: Aho–Corasick (`aho`)

**Build.** Insert all patterns into a trie (one dict of children per state, so memory is proportional to the number of edges, not 95 slots per state). `term[i]` is the end state of pattern `i`; duplicate patterns end in the same state, so they share it and get equal counts. Failure links are computed in BFS order: for a child `v` of `u` with character `c`, follow the failure links of `u` until a state with an edge `c` exists (or the root); that target is `fail[v]`. A failure link points to a strictly shallower state, so BFS order guarantees it is already known.

**Query for one text.** Start in the root; for each character follow failure links until an edge exists, then step, and increment a visit counter of the reached state. Patterns that are suffixes of the visited string (such as `he` inside `she`) must also be counted. Instead of walking the failure chain at every position, add each state's visit count to its failure target in reverse BFS order (deepest states first): `vis[fail[u]] += vis[u]`. After this pass `vis[term[i]]` equals the number of occurrences of pattern `i`, including overlaps and suffix patterns. The counters are recreated for every text, so texts are independent. The output row for a text has one value per original dictionary position.

**Boundaries.** An empty dictionary gives an empty row per text; no texts gives `[]`; empty texts give rows of zeros; duplicates; overlaps; dense input (400 patterns `a^k`, 100 texts of `a^2000`, total text length 200000, tested).

**Complexity.** Let `L` be the total pattern length, `S` the number of states, `p` the number of patterns. Construction is O(L) for the trie plus O(S) amortized for failure links (walks are amortized along pattern paths); for the contract's fixed alphabet of 95 characters this is within the allowed O(L + 95·S + p). A scan of one text is amortized O(|text|) for the transitions plus O(S + p) for the propagation and the output row. Memory is O(S + p) auxiliary and O(q·(p+1)) output for `q` texts. No quadratically copied output lists are created.

## 4. Own tests (`tests/student/`)

`tests/student/test_student.py` has 63 checks, all passed (`tests/student/test_results.txt`); the repeated-request file is `tests/student/cases.jsonl` and its actual output is `tests/student/cases_actual.txt`. Small cases are compared with independent brute-force oracles (all subsets for LCS and tree sets, exhaustive merge-order search for blocks, a `startswith`-based reference for searching and counting, sorting whole suffix strings for the suffix array); large cases use validators.

| Test group | Defect it detects |
|---|---|
| LCS: published example, empty strings, identical, disjoint, 300 random vs brute force, `1000 × ~667` and `1000 × 1000` | wrong base case, treating the result as a substring, wrong reconstruction, off-by-one in the table, too slow at the limit |
| Merge: published example, `n = 0, 1`, zeros, 200 random vs exhaustive search, `n = 200` with `10⁹`, validator rejects a non-adjacent plan | greedy choice, non-adjacent merges, wrong plan order (parent before child), wrong cost, 64-bit overflow |
| Tree: published example, empty, single vertex, all negative, 300 random trees vs brute force, chain and star with 100000 vertices, chain of `-10⁹` | recursion failure on deep chains, taking adjacent vertices, forgetting the empty set, wrong parent restriction in reconstruction |
| naive/kmp/rk: overlaps, empty pattern, both empty, pattern longer than text, case and spaces, 300 random vs reference, three methods agree at `n = 3000`, KMP at `200000 / 100000`, RK at `5000 × 4000` | missed last start, lost overlaps, empty-pattern boundary, case folding, bad fallback after a match |
| RK collision: `ab` and `dj` share hash 75; repeated collisions | reporting hash-equal windows without character verification, negative modulo |
| Suffix: `banana` (expected `sa`), empty, one character, no repeat, 300 random vs sorted suffixes, `n = 50000` all-equal, random and periodic | wrong order of suffixes that are prefixes of others, non-maximal LCP, empty-text handling, repeated string with wrong length, slowness |
| Aho: published example, empty dictionary, no texts, overlaps, 200 random vs reference, dense limit input | missing suffix-pattern counts (`he` inside `she`), duplicate dictionary entries, state leaking between texts, slow per-match traversal |
| `main.py` mixed batch repeated twice | state leaking between requests and between different tasks, stdout contamination |

The test script also contains a negative test for the merge validator (a non-adjacent plan must be rejected), which shows that the validator can fail.

## 5. Benchmark: naive vs KMP vs exact Rabin–Karp

**Setup.** `tests/student/benchmark.py`, seed 2026 (`random.Random(2026)`). Two input families with the same inputs for all three methods (the script asserts that all three return identical positions):

- *random*: text and pattern over the alphabet `abcd`.
- *adversarial for naive*: text `a^n`, pattern `a^(m−1)b` (every start matches `m−1` characters before failing).

Sizes `(n, m)`: `(1000, 100)`, `(2000, 200)`, `(3000, 300)`, valid for the limits of all three methods.

- Environment: macOS 14.6 (arm64, Apple Silicon), Python 3.14.0 (CPython). Hardware: `<MacBook Air 13, chip m3, RAM 8>`.
- Timer: `time.perf_counter()`; `gc.collect()` before each timed run.
- Warm-up: 1 untimed run per method per input; timed runs: 5 per method per input; the median is reported.
- Timing boundary: only the call of the algorithm function with the already-built request. Input generation, JSON parsing and process start-up are excluded. There is no compilation step.
- Command: `python3 tests/student/benchmark.py > tests/student/benchmark_results.txt` (the full raw output is in that file).

**Raw timings (seconds, 5 runs).**

Random:

| n | m | naive | KMP | RK |
|---|---|---|---|---|
| 1000 | 100 | 6e-05 ×5 | 6e-05 ×5 | 0.00013 ×5 |
| 2000 | 200 | 0.00012 ×5 | 0.00012 ×5 | 0.00026 ×5 |
| 3000 | 300 | 0.00018 ×5 | 0.00018 ×5 | 0.00039, 0.00039, 0.00039, 0.00038, 0.00038 |

Adversarial:

| n | m | naive | KMP | RK |
|---|---|---|---|---|
| 1000 | 100 | 0.0035, 0.00346, 0.00352, 0.00353, 0.00359 | 9e-05, 0.0001, 9e-05, 0.0001, 0.0001 | 0.00012, 0.00013, 0.00013, 0.00013, 0.00013 |
| 2000 | 200 | 0.01329, 0.01357, 0.0135, 0.0137, 0.01373 | 0.00019 ×5 | 0.00025 ×5 |
| 3000 | 300 | 0.03072, 0.03116, 0.03061, 0.03041, 0.03104 | 0.0003 ×5 | 0.00039, 0.00038, 0.00038, 0.00038, 0.00038 |

**Medians (seconds).**

| Family | n | m | naive | KMP | RK |
|---|---|---|---|---|---|
| random | 1000 | 100 | 0.00006 | 0.00006 | 0.00013 |
| random | 2000 | 200 | 0.00012 | 0.00012 | 0.00026 |
| random | 3000 | 300 | 0.00018 | 0.00018 | 0.00039 |
| adversarial | 1000 | 100 | 0.00352 | 0.00010 | 0.00013 |
| adversarial | 2000 | 200 | 0.01357 | 0.00019 | 0.00025 |
| adversarial | 3000 | 300 | 0.03072 | 0.00030 | 0.00038 |

**Discussion.** On random text over four letters naive mismatches after about one character on average, so it behaves almost linearly and is as fast as KMP; RK is about twice as slow because it does a multiplication and a modulo for every character. On the adversarial family naive grows roughly quadratically: when `n` and `m` double, its median grows about 3.9 times (0.00352 to 0.01357), and when they triple it grows about 8.7 times (0.00352 to 0.03072), close to the factors 4 and 9 of the `n·m` model. KMP (0.0001, 0.00019, 0.0003) and RK (0.00013, 0.00025, 0.00038) grow about linearly. Here RK is linear because the all-`a` windows have a hash different from the pattern's, so there are no equal-hash candidates to verify; RK's worst case (many collisions with modulus 101) was not benchmarked, and the analysis above states that it can reach O(n·m). The random-family times (tens of microseconds) are small compared with timer and interpreter noise, so only the ratios between methods, not the absolute values, should be read from that family. The conclusions apply to this implementation, these input families and this machine.

## 6. Sources and AI assistance

Sources: course lectures and the assignment specification (`README.md`, `docs/guide/CONTRACTS.md`); the standard textbook algorithms (prefix-DP LCS, interval DP, tree DP, KMP, Rabin–Karp, prefix doubling, Kasai, Aho–Corasick) as described in *Introduction to Algorithms* (Cormen et al.). `main.py`, `tools/run.py` and the public cases were supplied by the course template.

AI assistance: Claude (Anthropic) was used to draft the algorithm code, the own-test script, the benchmark script and this document. All commands above were run locally by the student, and all results and numbers in this document come from the student's own runs. `<Student: Nurdaulet edit this paragraph to match the exact acknowledgement format required by the syllabus, and state which parts you wrote, reviewed and understood yourself.>`
