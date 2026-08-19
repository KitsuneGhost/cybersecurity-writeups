# Cybersecurity Writeups

A collection of my writeups and notes from Hack The Box machines, binary
exploitation challenges, CTFs, and security research.

The goal of this repository is to document not only the commands and payloads I
used, but also the reasoning behind them: how I identified an attack surface,
why an exploit worked, and what defenders can learn from the vulnerability.

> [!IMPORTANT]
> All testing documented here was performed in intentionally vulnerable labs,
> CTF environments, or other systems for which I had explicit authorization.
> Do not use these techniques against systems without permission.

## Writeups

### Hack The Box machines

| Machine | OS | Difficulty | Key topics | Writeup |
| --- | --- | --- | --- | --- |
| Cohort | Linux (Ubuntu) | — | API enumeration, command injection, PackageKit TOCTOU race | [Read](htb/machines/cohort/) |
| Nexus | Linux (Ubuntu) | Easy | Git history secrets, authenticated file upload, password reuse, path traversal | [Read](htb/machines/nexus/) |

### Hack The Box challenges

| Challenge | Category | Difficulty | Key topics | Writeup |
| --- | --- | --- | --- | --- |
| RAuth | Reversing | Easy | Binary patching, Salsa20, XMM constant extraction | [Read](htb/challenges/rauth/) |

### CTF challenges

| Challenge | Event | Category | Key topics | Writeup |
| --- | --- | --- | --- | --- |
| wpm-game | scriptCTF 2026 | Web | Python `eval()` injection, blacklist bypass, error-based file disclosure | [Read](scriptCTF-2026/wpm-game/) |
| F**K | scriptCTF 2026 | Reversing | Brainfuck analysis, instruction-count side channel, automated recovery | [Read](scriptCTF-2026/F%2A%2AK/) |
| Diabolical | scriptCTF 2026 | Reversing | Static analysis, embedded data, Base64 decoding | [Read](scriptCTF-2026/diabolical/) |

## Repository structure

```text
.
├── htb/
│   ├── challenges/
│   │   └── rauth/
│   └── machines/
│       ├── cohort/
│       └── nexus/
├── scriptCTF-2026/
│   ├── diabolical/
│   ├── F**K/
│   └── wpm-game/
└── templates/
    ├── htb-machine-template.md
    └── pwn-template.md
```

- `htb/machines/` contains retired Hack The Box machine writeups.
- `htb/challenges/` contains standalone Hack The Box challenge writeups.
- `scriptCTF-2026/` contains challenge writeups and supporting exploit code from
  scriptCTF 2026.
- `templates/` contains reusable outlines for new writeups.

## Principles

- Explain the reasoning, not just the commands.
- Include enough detail to reproduce the result in an authorized lab.
- Describe the vulnerability's root cause and possible remediation.
- Credit external research, tools, and challenge authors.
- Do not publish active-machine solutions, flags, credentials, VPN files, or
  other secrets.

## Disclaimer

This repository is for educational purposes only. The material is provided
without warranty, and I am not responsible for misuse. Always obtain explicit
authorization before testing a system.

Challenge files and third-party material remain the property of their
respective owners.
