# scriptCTF 2026 — Diabolical (Reversing)

- **Author:** NoobMaster
- **Category:** Reversing
- **Description:** *"scriptCTF does not have hard reversing challenges" — Armored Pawn. Let's see about that shall we?*

## Overview

The `vault` binary is a Go program wrapped in layers of deliberately hostile obfuscation — AES-GCM "unwrapping", scattered XOR-masked keys, anti-debug traps, opaque predicates, and an input gate that can **never** succeed by construction. None of it matters. The flag sits in plaintext as a **base64 trailer** on the binary:

```bash
strings vault | tail -1
# c2NyaXB0Q1RGe24wdF9zMF9oNHJkXzRmdDNyXzRsbH0=

echo 'c2NyaXB0Q1RGe24wdF9zMF9oNHJkXzRmdDNyXzRsbH0=' | base64 -d
# scriptCTF{n0t_s0_h4rd_4ft3r_4ll}
```

*"Let's see about that shall we?"* — turns out it was **not so hard after all** (read the flag).

## Recon

```bash
$ file vault
vault: ELF 64-bit LSB executable, x86-64, statically linked, Go BuildID=...
```

A statically-linked Go binary. The usual first move for Go binaries is `strings` (Go keeps most string data plaintext in `.rodata`):

```bash
$ strings vault | tail -20
...
  ┌────────────────────────────────────┐
  │   V A U L T   //   sector 0x1f     │
  │   authorized personnel only        │
  └────────────────────────────────────┘
  key>
  validating
  [+] gate released
  [-] rejected — sequence does not authenticate
  c2NyaXB0Q1RGe24wdF9zMF9oNHJkXzRmdDNyXzRsbH0=
```

The **last line** is base64. One decode later:

```bash
$ echo 'c2NyaXB0Q1RGe24wdF9zMF9oNHJkXzRmdDNyXzRsbH0=' | base64 -d
scriptCTF{n0t_s0_h4rd_4ft3r_4ll}
```

Done.

## Why This Works (and What You're *Supposed* to Be Afraid Of)

The attached source (`src/vault.go`) shows what the author packed into the binary — and why none of it stops `strings`:

### 1. Unicode-confusable identifiers

```go
import (
	ᴀ "crypto/aes"
	ʙ "crypto/cipher"
	ʜ "crypto/hmac"
	ꜱ "crypto/sha256"
	ʙʙ "bufio"
	ꜰ "fmt"
	ᴏ "os"
	ꜱᴛ "strings"
	ᴅ "syscall"
	ᴛ "time"
)
```

Every package is aliased to a lookalike Unicode character (`ᴀ`≈A, `ʙ`≈B, `ꜱ`≈S, `ᴏ`≈O, …). This defeats naive greps and makes the decompiled code a wall of noise.

### 2. Scattered, XOR-masked key material

The AES-GCM key, nonce, and ciphertext are split across globals (`qA`, `qB`, `qM`, `qP`, `qC`, `qN`) and reassembled at runtime via a XOR fold (`lI`). Static analysis can't just read a key out of `.rodata` — the key only exists transiently on the stack during `I1()`.

### 3. Anti-debugging

```go
func init() {
	if zP() { q0 = true }                 // TracerPid != 0/ppid  → traced
	if _, _, e := ᴅ.Syscall(ᴅ.SYS_PTRACE, 0, 0, 0); e != 0 {
		q0 = true                          // PTRACE_TRACEME failed → already traced
	}
}
```

- `PTRACE_TRACEME` claims the process for a tracer; if it fails, something is already debugging it.
- `/proc/self/status` `TracerPid` is scraped both at `init` and later (`zW()`).
- If a tracer is detected, the key byte is XOR-perturbed so **GCM authentication fails** — the vault "refuses" with no breakpointable failure.

### 4. An input gate that can never open

```go
func lll(in []byte) []byte {           // HMAC-SHA256 of input + length mix
	m := ʜ.New(ꜱ.New, []byte{0x2a, 0x2a, 0x2a})
	m.Write(in)
	m.Write([]byte{byte(ll(uint64(len(in)), 5))})
	return m.Sum(nil)
}
```

`main` compares `SHA256(HMAC(key))` against `SHA256(vault_contents)` — but the candidate is derived **only from operator input**, so by construction it can never equal the actual vault block. The "gate released" branch is unreachable dead logic; there is no correct password. The author even left the comment: *"by construction this can never equal the block that produced the vault, so the gate below never opens."*

### 5. Opaque predicates and noise

```go
func O0(n int) bool {            // always true: n²+n is always even
	x := (n*n + n)
	return x%2 == 0
}
```

plus a xorshift/xorwow-style mixer (`ll`) to fatten the call graph. Pure noise.

## The Lesson

Every layer — AES-GCM, anti-trace detection, impossible HMAC gate, unicode aliasing — protects a secret that **isn't in the logic at all**. The real flag was appended to the binary as a static base64 string (the source dir even contains `vault.pre-trailer-fix.bak`, hinting the trailer was a deliberate addition). For reversing, the cheapest attack is still the first one: **read the strings before you read the code**.

## Flag Format

```
scriptCTF{...}
```

## Takeaways

1. **Start with `strings`/`file`/`binwalk` on every binary** — embedded data (base64, URLs, keys) is the most common shortcut.
2. **Obfuscation protects code paths, not data blobs** — anything stored as a literal can be read without executing a single instruction.
3. **Time-box deep reversing** — if a binary is engineered to be hostile (anti-debug + impossible gates), that's often a sign the intended path is *outside* the code.
4. If you *do* need the deep path, the tools of choice here would be `gdb` with `catch syscall ptrace` patching (to defeat the anti-debug) and then breaking after `I1()` to dump the decrypted vault — but that's the hard way, and the challenge name says it all.
