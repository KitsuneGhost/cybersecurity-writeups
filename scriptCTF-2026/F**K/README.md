# scriptCTF 2026 — F**k (Reversing)

- **Author:** ConnorChang
- **Category:** Reversing
- **Description:** *ABSOLUTELY NO SWEARING IS PERMITTED*

## Overview

`funk` is a generated, heavily-obfuscated **Brainfuck** program that checks a 31-character input against the flag. It never terminates because it ends with a `+[]` infinite loop — remove that trailer and the program exits. The number of **executed instructions** then leaks the flag character-by-character: for each input position, the correct character zeroes the corresponding cell, which makes nearby junk loops **skip their bodies**, measurably dropping the instruction count. Brute-forcing each position for the minimum instruction count recovers:

```
scriptCTF{t1mm1ng_s1d$_ch@nn31}
```

*(Yes — "timing side channel".)*

## Recon

```bash
$ file funk
funk: ASCII text

$ tail -c 40 funk
...>]<<<<<<<<<<<<<<<<<[-<++++++++++>]<++++++++[-<->]>[-]<[->-<]... +[]
```

The attachment is not a compiled binary at all — it's a plain-text **Brainfuck program** (hence the challenge name). The very last characters are:

```
+[]
```

`+` makes the current cell nonzero, and `[]` then loops forever: **any input hangs**. The comment in the source (`gen.py`) confirms it: `+[]` was appended deliberately as an unconditional infinite loop with no other purpose — it's safe to delete.

## Behavior After the Fix

Delete the trailing `+[]`:

```bash
head -c -3 funk > funk_fixed
```

Now the program:
1. Reads **31 characters** from stdin into cells `arr+0 … arr+30`
2. Performs one check block per input position (in a shuffled order)
3. Exits

Run it and it accepts anything — but observe the **instruction count**:

```bash
$ echo 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' | ./some_bf_interpreter -c funk_fixed
...  # N instructions executed
$ echo 'scriptCTF{t1mm1ng_s1d$_ch@nn31}' | ./some_bf_interpreter -c funk_fixed
...  # N-Δ instructions executed
```

Different inputs execute different numbers of instructions — a textbook **side channel**.

## Understanding the Generator (`src/gen.py`)

The author shipped the generator that produced `funk`. It builds the flag check from three primitives:

### 1. The check block (per flag byte `c` at shuffled position `j`)

```python
def block(r, cur, pos, tmp, c):
    s  = mv(cur, pos)            # move to input cell arr+j
    x  = salt(r)                 # random salt 17..89
    s += run("+", x, r)          # cell[pos] = input[j] + x
    s += mv(cur, tmp + 1)
    t, *_ = con(c + x, r)        # cell[tmp] = c + x   (via multiply-add loops)
    s += "[-" + mv(tmp, pos) + "-" + mv(pos, tmp) + "]"   # cell[pos] -= (c+x)
    s += mv(tmp, pos) + "[-]"    # zero tmp
    return s, cur
```

Walking through the arithmetic:

```
cell[pos] = input[j] + x      (salt)
cell[tmp] = c + x             (constant, precomputed via loops)
loop: cell[tmp]--, cell[pos]--   → runs exactly c+x times
⇒ cell[pos] = input[j] + x − (c + x) = input[j] − c
```

**If `input[j] == c`, the cell ends at exactly 0. Otherwise it is nonzero** (wrapping mod 256 if negative). The positions are shuffled (`r.shuffle(ord)`) but each block touches only its own input cell — the checks are **independent per position**.

### 2. Junk — the side channel itself

```python
def junk(r, cur, base, sp=400):
    ...
    if x < .7:
        s += "[" + fake(r.randint(1, 255), r) + "]"
    else:
        s += "[" + "".join(r.choice("><+-.,") ...) + "]"
    ...
```

Junk is sprinkled after reads and between blocks as `[ <fake body> ]`. A Brainfuck `[` loop **skips its body entirely if the current cell is 0** — and junk after block `j` sits exactly on cell `arr+j`, the cell that is 0 **iff your guess for position `j` was correct**.

```
correct char  → cell == 0  → junk body skipped  → fewer instructions
wrong char    → cell != 0  → junk body executed  → more instructions
```

The total instruction count is therefore roughly:

```
count = constant + Σ over positions ( junk_cost(j) if guess_j != flag_j else 0 )
```

Each position contributes independently — so we can brute-force **one position at a time**.

### 3. The infinite loop

```python
ans.append(mv(cur, play))
ans.append("+[]")     # unconditional hang — must be removed
```

## Exploit

A small Brainfuck interpreter that counts executed instructions (bodies of skipped `[...]` loops are not counted — that's the signal):

```python
def run(code, inp):
    cells, ptr, ip, ins = [0]*1000, 0, 0, 0
    inp = list(inp)
    while ip < len(code):
        c = code[ip]; ins += 1
        if   c == '>': ptr += 1
        elif c == '<': ptr -= 1
        elif c == '+': cells[ptr] = (cells[ptr] + 1) & 0xff
        elif c == '-': cells[ptr] = (cells[ptr] - 1) & 0xff
        elif c == ',': cells[ptr] = ord(inp.pop(0)) if inp else 0
        elif c == '[' and cells[ptr] == 0:      # skip matching ]
            d = 1
            while d:
                ip += 1
                d += (code[ip] == '[') - (code[ip] == ']')
        elif c == ']' and cells[ptr] != 0:      # jump back to matching [
            d = 1
            while d:
                ip -= 1
                d += (code[ip] == ']') - (code[ip] == '[')
        ip += 1
    return ins

code = open("funk").read().replace("+[]", "")   # remove the hang

flag = ""
charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_{}$@!-"
for pos in range(31):                            # brute force each position
    best = min(
        ((run(code, (flag + ch + "a"*(30-pos)).ljust(31, "a")[:31]), ch)
         for ch in charset),
        key=lambda t: t[0])
    flag += best[1]
    print(f"pos {pos:2d}: {flag!r}  ({best[0]} ins)")

print("FLAG:", flag)
```

Output (abridged):

```
pos  0: 's'  (312840 ins)
pos  1: 'c'  (312510 ins)
...
pos 30: '}'  (299102 ins)
FLAG: scriptCTF{t1mm1ng_s1d$_ch@nn31}
```

For each position the **minimum** instruction count occurs at the correct character — the junk loop for that position is skipped, saving ~300 instructions per wrong guess.

## Flag

```
scriptCTF{t1mm1ng_s1d$_ch@nn31}
```

## Takeaways

1. **Always run the binary before reversing it** — here, running exposed the hang, and the `+[]` trailer was visible at the end of the file. `file`/`tail`/`strings` cost nothing.
2. **Timing/instruction-count side channels are a valid reversing technique** — a constant-time bug (`the program does more work when a check fails`) is a full oracle, no need to understand the obfuscation.
3. **Junk code designed to mislead still leaks through its own control flow** — the "junk" loops are exactly what makes the check measurable. Zeroing a cell is only secret if nothing later branches on it.
4. **Look for the generator** — CTF authors often ship `src/`; reading `gen.py` collapses the whole binary into a 100-line program.
