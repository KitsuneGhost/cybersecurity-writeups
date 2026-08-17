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
| _Coming soon_ | — | — | — | — |

### Pwn challenges

| Challenge | Event / Platform | Architecture | Mitigations | Writeup |
| --- | --- | --- | --- | --- |
| _Coming soon_ | — | — | — | — |

## Repository structure

```text
.
├── htb/
│   └── machines/
├── pwn/
├── assets/
└── templates/
    ├── htb-machine-template.md
    └── pwn-template.md
```

- `htb/machines/` contains retired Hack The Box machine writeups.
- `pwn/` contains binary-exploitation challenge writeups and supporting code.
- `assets/` contains sanitized screenshots and diagrams.
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
