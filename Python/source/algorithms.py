"""Assignment 4: DP and string processing (iterative, no recursion)."""


def lcs(request):
    a, b = request["a"], request["b"]
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    i, j, out = n, m, []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return {"length": dp[n][m], "sequence": "".join(reversed(out))}


def merge(request):
    sizes = request["sizes"]
    n = len(sizes)
    if n <= 1:
        return {"cost": 0, "plan": []}
    pre = [0] * (n + 1)
    for i, s in enumerate(sizes):
        pre[i + 1] = pre[i] + s
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for l in range(0, n - length + 1):
            r = l + length - 1
            total = pre[r + 1] - pre[l]
            best, bk = None, l
            for k in range(l, r):
                c = dp[l][k] + dp[k + 1][r]
                if best is None or c < best:
                    best, bk = c, k
            dp[l][r] = best + total
            split[l][r] = bk
    # preorder (parent before children), reversed => children before parent
    pre_order = []
    stack = [(0, n - 1)]
    while stack:
        l, r = stack.pop()
        if l < r:
            k = split[l][r]
            pre_order.append([l, k, r])
            stack.append((l, k))
            stack.append((k + 1, r))
    pre_order.reverse()
    return {"cost": dp[0][n - 1], "plan": pre_order}


def tree(request):
    n = request["n"]
    weights = request["weights"]
    edges = request["edges"]
    if n == 0:
        return {"weight": 0, "selected": []}
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    parent = [-1] * n
    order = [0]
    seen = [False] * n
    seen[0] = True
    for u in order:  # BFS; list grows while iterating
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True
                parent[v] = u
                order.append(v)
    take = [weights[v] for v in range(n)]
    skip = [0] * n
    for v in reversed(order):
        p = parent[v]
        if p != -1:
            take[p] += skip[v]
            skip[p] += max(take[v], skip[v])
    chosen = [False] * n
    for v in order:
        p = parent[v]
        if p == -1 or not chosen[p]:
            chosen[v] = take[v] > skip[v]
    selected = [v for v in range(n) if chosen[v]]
    return {"weight": max(take[0], skip[0]), "selected": selected}


def _all_boundaries(n):
    return list(range(n + 1))


def naive(request):
    text, pattern = request["text"], request["pattern"]
    n, m = len(text), len(pattern)
    if m == 0:
        return {"positions": _all_boundaries(n)}
    out = []
    for i in range(n - m + 1):
        j = 0
        while j < m and text[i + j] == pattern[j]:
            j += 1
        if j == m:
            out.append(i)
    return {"positions": out}


def kmp(request):
    text, pattern = request["text"], request["pattern"]
    n, m = len(text), len(pattern)
    if m == 0:
        return {"positions": _all_boundaries(n)}
    pi = [0] * m
    k = 0
    for i in range(1, m):
        while k and pattern[i] != pattern[k]:
            k = pi[k - 1]
        if pattern[i] == pattern[k]:
            k += 1
        pi[i] = k
    out = []
    k = 0
    for i in range(n):
        while k and text[i] != pattern[k]:
            k = pi[k - 1]
        if text[i] == pattern[k]:
            k += 1
        if k == m:
            out.append(i - m + 1)
            k = pi[k - 1]
    return {"positions": out}


def rk(request):
    text, pattern = request["text"], request["pattern"]
    n, m = len(text), len(pattern)
    if m == 0:
        return {"positions": _all_boundaries(n)}
    if m > n:
        return {"positions": []}
    base, mod = 31, 101
    high = 1
    for _ in range(m - 1):
        high = (high * base) % mod
    ph = wh = 0
    for i in range(m):
        ph = (ph * base + ord(pattern[i])) % mod
        wh = (wh * base + ord(text[i])) % mod
    out = []
    for i in range(n - m + 1):
        if wh == ph:  # candidate only: verify real characters
            j = 0
            while j < m and text[i + j] == pattern[j]:
                j += 1
            if j == m:
                out.append(i)
        if i + m < n:
            wh = ((wh - ord(text[i]) * high) * base + ord(text[i + m])) % mod
    return {"positions": out}


def suffix(request):
    text = request["text"]
    n = len(text)
    if n == 0:
        return {"sa": [], "lcp": [], "repeated": ""}
    big = max(n, 128) + 2
    rank = [ord(c) for c in text]
    sa = list(range(n))
    k = 1
    while True:
        key = [rank[i] * big + (rank[i + k] + 1 if i + k < n else 0) for i in range(n)]
        sa.sort(key=key.__getitem__)
        tmp = [0] * n
        for idx in range(1, n):
            tmp[sa[idx]] = tmp[sa[idx - 1]] + (1 if key[sa[idx]] != key[sa[idx - 1]] else 0)
        rank = tmp
        if rank[sa[-1]] == n - 1:
            break
        k *= 2
    lcp = [0] * n
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = sa[rank[i] - 1]
            while i + h < n and j + h < n and text[i + h] == text[j + h]:
                h += 1
            lcp[rank[i]] = h
            if h > 0:
                h -= 1
        else:
            h = 0
    best = max(lcp)
    repeated = ""
    if best > 0:
        pos = lcp.index(best)
        repeated = text[sa[pos]:sa[pos] + best]
    return {"sa": sa, "lcp": lcp, "repeated": repeated}


def aho(request):
    patterns, texts = request["patterns"], request["texts"]
    nxt = [{}]
    term = []
    for p in patterns:
        s = 0
        for ch in p:
            t = nxt[s].get(ch)
            if t is None:
                t = len(nxt)
                nxt.append({})
                nxt[s][ch] = t
            s = t
        term.append(s)
    states = len(nxt)
    fail = [0] * states
    order = []
    queue = list(nxt[0].values())
    for v in queue:
        fail[v] = 0
    qi = 0
    while qi < len(queue):
        u = queue[qi]
        qi += 1
        order.append(u)
        for ch, v in nxt[u].items():
            f = fail[u]
            while f and ch not in nxt[f]:
                f = fail[f]
            fail[v] = nxt[f].get(ch, 0)
            queue.append(v)
    counts = []
    for text in texts:
        vis = [0] * states
        s = 0
        for ch in text:
            while s and ch not in nxt[s]:
                s = fail[s]
            s = nxt[s].get(ch, 0)
            vis[s] += 1
        for u in reversed(order):
            vis[fail[u]] += vis[u]
        counts.append([vis[t] for t in term])
    return {"counts": counts}