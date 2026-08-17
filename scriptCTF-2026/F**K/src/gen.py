import random

def salt(r):
    x = r.randint(17, 89)
    if x % 10 == 0:
        x += 3
    return x

def noise(r, n=None):
    if n is None:
        n = r.randint(2, 6)
    a = ["+"] * n + ["-"] * n
    r.shuffle(a)
    return "".join(a)

def run(op, cnt, r):
    s = ""
    if r.random() < .4:
        s += noise(r)
    while cnt:
        x = r.randint(1, min(cnt, 5))
        s += op * x
        cnt -= x
        s += noise(r)
    return s

def con(v, r):
    if v <= 3:
        return run("+", v, r), 0, 0, v
    k = r.randint(2, min(12, v))
    m = v // k
    rem = v - k * m
    s = run("+", k, r)
    s += "[-<" + run("+", m, r) + ">]"
    s += "<" + run("+", rem, r)
    return s, k, m, rem

def wig(r):
    x = r.randint(2, 5)
    return ">" * x + "<" * x

def mv(a, b):
    if a < b:
        return ">" * (b - a)
    return "<" * (a - b)

def fake(c, r):
    s = ""
    s += wig(r)
    x = salt(r)
    s += run("+", x, r)
    s += ">>"
    t, *_ = con(c + x, r)
    s += t
    s += wig(r)
    s += "[-<->]"
    s += wig(r)
    s += "<[-]"
    return s

def junk(r, cur, base, sp=400):
    x = r.random()
    if x < .35:
        return wig(r), cur

    p = base + r.randint(0, sp)
    s = mv(cur, p)

    if x < .7:
        s += "[" + fake(r.randint(1, 255), r) + "]"
    else:
        c = "><+-.,"
        s += "[" + "".join(r.choice(c) for _ in range(r.randint(4, 10))) + "]"

    s += mv(p, cur)
    return s, cur

def block(r, cur, pos, tmp, c):
    s = ""

    s += mv(cur, pos)
    cur = pos

    x = salt(r)
    s += run("+", x, r)

    s += mv(cur, tmp + 1)
    cur = tmp + 1

    t, *_ = con(c + x, r)
    s += t
    cur = tmp

    s += "[-"
    s += mv(tmp, pos)
    s += "-"
    s += mv(pos, tmp)
    s += "]"

    s += mv(tmp, pos)
    cur = pos

    s += "[-]"

    return s, cur

flag = "scriptCTF{t1mm1ng_s1d$_ch@nn31}"
r = random.Random()

f = flag.encode()
n = len(f)

ord = list(range(n))
r.shuffle(ord)

arr = 0
tmp = n
play = n * 3

ans = []
cur = 0

for i in range(n):
    ans.append(mv(cur, arr + i))
    cur = arr + i
    ans.append(",")
    if r.random() < .3:
        x, cur = junk(r, cur, play)
        ans.append(x)

for i, j in enumerate(ord):
    x, cur = block(r, cur, arr + j, tmp + i * 2, f[j])
    ans.append(x)
    if r.random() < .5:
        y, cur = junk(r, cur, play)
        ans.append(y)

ans.append(mv(cur, play))
ans.append("+[]")

print("".join(ans))
