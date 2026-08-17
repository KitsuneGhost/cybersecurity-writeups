# Machine Name

> Do not publish this writeup until the machine has retired and publication is
> permitted by Hack The Box.

| Field | Value |
| --- | --- |
| Platform | Hack The Box |
| Operating system | Linux / Windows |
| Difficulty | Easy / Medium / Hard / Insane |
| Machine IP | `10.10.11.X` |
| Date completed | YYYY-MM-DD |
| Key topics | Topic 1, Topic 2, Topic 3 |

## Summary

Briefly describe the attack path without including flags. Mention the initial
entry point, the privilege-escalation technique, and the main lesson learned.

## Enumeration

### Port scanning

```bash
nmap -p- --min-rate 5000 -oA scans/all-ports 10.10.11.X
nmap -sC -sV -p PORTS -oA scans/services 10.10.11.X
```

Summarize the exposed services and explain which ones deserve further
investigation.

| Port | Service | Version | Notes |
| ---: | --- | --- | --- |
|  |  |  |  |

### Service and web enumeration

Document discoveries such as virtual hosts, endpoints, shares, users, or
application behavior. Explain how each discovery affected the next step.

```bash
# Relevant command
```

## Initial access

### Vulnerability

Describe the vulnerability or misconfiguration and its root cause. Include any
failed hypotheses that were important to narrowing down the attack path.

### Exploitation

Explain the payload or procedure before showing it.

```bash
# Exploitation command or sanitized proof of concept
```

Describe the access obtained and the affected user. Do not include the user
flag, passwords, session tokens, or reusable credentials.

## Privilege escalation

### Local enumeration

```bash
# Relevant enumeration commands
```

Highlight the specific permissions, services, credentials, or configuration
that created the escalation path.

### Exploitation

Explain why the technique works, then document the minimum reproducible steps.

```bash
# Privilege-escalation commands
```

Describe the resulting privilege level without publishing the root flag.

## Attack path

```text
External enumeration
  -> vulnerable service or application
  -> initial access as USER
  -> local misconfiguration or vulnerability
  -> administrative access
```

## Remediation

- Explain how to remove or mitigate the initial-access vulnerability.
- Explain how to prevent the privilege-escalation path.
- Mention useful detection opportunities or indicators where applicable.

## Lessons learned

- What was the most important technical lesson?
- What assumption or dead end cost the most time?
- What would you do differently next time?

## References

- [Reference title](https://example.com)

