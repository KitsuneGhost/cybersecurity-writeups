# scriptCTF 2026 Writeups

Writeups for the challenges I solved during scriptCTF 2026. These notes focus
on the reasoning behind each solution: identifying the important behavior,
working around constraints, and understanding why the final exploit works.

## Challenges

| Challenge | Category | Key concepts |
| --- | --- | --- |
| [wpm-game](wpm-game/) | Web | Python `eval()` injection, blacklist bypass, file disclosure through error messages |
| [F**K](F%2A%2AK/) | Reversing | Brainfuck analysis, instruction-count side channel, automated recovery |
| [Diabolical](diabolical/) | Reversing | Static analysis, embedded data, Base64 decoding, avoiding obfuscation traps |

## Repository layout

Each challenge directory contains a `README.md` explaining the solution and,
where applicable, the original challenge files and a cleaned exploit script.

```text
scriptCTF-2026/
├── README.md
├── wpm-game/
│   ├── README.md
│   ├── exploit.py
│   └── src/
├── F**K/
│   ├── README.md
│   ├── exploit.py
│   └── src/
└── diabolical/
    ├── README.md
    └── src/
```

## Disclaimer

These writeups document challenges from an intentionally vulnerable CTF
environment. They are provided for educational purposes only. Do not apply the
techniques against systems without explicit authorization.

Challenge names, descriptions, and distributed files belong to their
respective authors and the scriptCTF organizers.
