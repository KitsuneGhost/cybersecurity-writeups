# Challenge Name

| Field | Value |
| --- | --- |
| Event / Platform |  |
| Category | Pwn |
| Difficulty |  |
| Architecture | amd64 / i386 / ARM / other |
| Date completed | YYYY-MM-DD |
| Key topics | Buffer overflow, ROP, heap, format string, etc. |

## Summary

Briefly describe the vulnerability, the exploitation strategy, and the main
lesson. Do not include a live competition's flag.

## Files

| File | Description | SHA-256 |
| --- | --- | --- |
| `challenge` | Challenge binary | `...` |
| `libc.so.6` | Supplied libc, if any | `...` |
| `ld-linux-*.so.*` | Supplied loader, if any | `...` |

Only redistribute challenge files when the event or author permits it.

## Initial analysis

### File information and mitigations

```bash
file ./challenge
checksec --file=./challenge
```

```text
Architecture:
RELRO:
Stack canary:
NX:
PIE:
Stripped:
```

Explain how these properties constrain the available exploitation strategies.

### Program behavior

Describe the input format, important menu options, and observable crashes or
unexpected behavior.

```bash
./challenge
```

### Static and dynamic analysis

Document the relevant functions, data structures, and control flow. Include
small decompiler or disassembly excerpts only when they clarify the bug.

```gdb
# Useful breakpoints and inspection commands
```

## Vulnerability

Identify the vulnerable operation and explain the root cause—for example, an
unchecked copy, use-after-free, integer truncation, or uncontrolled format
string.

```c
/* Minimal pseudocode illustrating the bug */
```

Describe the primitive it provides, such as instruction-pointer control, an
arbitrary read, an arbitrary write, or a memory leak.

## Exploitation strategy

Outline the exploit before presenting the code.

1. Determine the offset or establish the required heap state.
2. Defeat relevant mitigations or leak required addresses.
3. Build the final read, write, ROP, or code-execution primitive.
4. Trigger the payload and verify execution.

### Finding the offset or primitive

```python
# Minimal experiment or cyclic-pattern example
```

### Address leaks and calculations

Show each important calculation and explain why the offset is valid for the
provided binary or library.

```text
leaked address - known symbol offset = library base
```

### Final exploit

```python
#!/usr/bin/env python3
from pwn import *

context.binary = elf = ELF("./challenge", checksec=False)
context.log_level = "info"


def start():
    if args.REMOTE:
        return remote("HOST", 1337)
    return process(elf.path)


io = start()

# Build and send the exploit here.

io.interactive()
```

Explain the important payload components; avoid leaving the reader with an
unannotated script.

## Verification

Show sanitized evidence that the exploit succeeds locally and, if permitted,
against the challenge service. Do not publish tokens, credentials, or flags.

## Remediation

Describe the source-level fix and any compiler or linker hardening that would
reduce exploitability. Mitigations are defense in depth, not substitutes for
fixing the underlying memory-safety issue.

## Lessons learned

- Which exploitation concept was most important?
- Which debugging technique helped the most?
- How could the exploit be made more reliable?

## References

- [Reference title](https://example.com)
