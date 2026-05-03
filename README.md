# 🌿 Hazel CLI v2.0

> **AI-Powered Cybersecurity Terminal Assistant**
> *Smart wrapper for your Linux terminal — built for pentesters & CTF players*

---

## 📋 Table of Contents

- [What is Hazel?](#what-is-hazel)
- [Features](#features)
- [File Structure](#file-structure)
- [Installation](#installation)
- [Getting API Keys (Free)](#getting-api-keys-free)
- [Adding API Keys to Hazel](#adding-api-keys-to-hazel)
- [Selecting AI Provider](#selecting-ai-provider)
- [All Commands](#all-commands)
- [AI Commands Demo](#ai-commands-demo)
- [Safety System](#safety-system)
- [Troubleshooting](#troubleshooting)

---

## What is Hazel?

Hazel sits between you and your terminal. Every command you type passes through Hazel first, which:

- **Fixes typos** before they cause damage (`namp` → `nmap`)
- **Warns about danger** before `rm -rf /` runs
- **Suggests next steps** after pentest tools run (`nmap` found port 80 → suggests `gobuster`)
- **Explains commands** so you actually learn what flags do
- **Answers questions** using free AI (`ask how do I enumerate SMB shares?`)
- **Writes your reports** automatically from session history

---

## Features

| Feature | How it works |
|---|---|
| ✏️ Typo Correction | `namp` → `nmap`, `sl` → `ls` (fuzzy matching) |
| ⚠️ Danger Detection | Blocks `rm -rf /`, `chmod 777`, fork bombs |
| 💡 Pentest Suggestions | Auto-suggests next tool based on scan output |
| 📖 Command Explainer | `explain nmap -sS -A` → full breakdown |
| 🤖 AI Q&A | `ask how to crack a hash` → AI answers |
| 🤖 AI Explain | `ai explain sqlmap --forms` → deeper explanation |
| 🤖 AI Suggestions | `ai suggest` → AI analyzes your session |
| 📝 Auto Writeup | `writeup` or `ai writeup` → pentest report |
| 🗄️ History | All commands saved to SQLite with timestamps |
| 🔄 AI Fallback | If AI fails → rule-based system still works |

---

## File Structure

```
hazel-cli/
│
├── run.py                  ← 🚀 Launch Hazel from here
├── cli.py                  ← REPL loop (prompt_toolkit)
├── interceptor.py          ← Command pipeline & routing
├── ai_engine.py            ← AI routing + multi-provider fallback
├── config.py               ← API key storage & provider manager
│
├── analyzer.py             ← Typo detection (difflib)
├── security.py             ← Dangerous command detection
├── suggestions.py          ← Rule-based pentest suggestions
├── history.py              ← SQLite command history
├── explain.py              ← Command explanation engine
├── writeup.py              ← Report generator
│
├── rules.json              ← All rules, patterns, explanations
├── requirements.txt        ← Python dependencies
├── .env                    ← Your API keys (auto-created, never commit)
├── .env.example            ← Key template
├── .gitignore              ← Protects .env from git
│
└── providers/
    ├── groq.py             ← Groq (Llama 3.3) — RECOMMENDED FREE
    ├── gemini.py           ← Google Gemini 2.0 Flash
    ├── openrouter.py       ← OpenRouter (Mistral 7B free)
    └── ollama.py           ← Local Ollama (no internet needed)
```

**Auto-created at runtime:**
- `hazel.db` — SQLite command history database
- `hazel_config.json` — active provider setting
- `.env` — your API keys (created by `set-api`)

---

## Installation

### Step 1 — Get the files

```bash
# Option A: Clone from GitHub
https://github.com/crypto-nidh/hazel-cli.git
cd hazel-cli

# Option B: Download and extract ZIP, then
cd hazel-cli
```

### Step 2 — Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependency

```bash
pip install prompt_toolkit
```

### Step 4 — Set up the alias (run once)

```bash
echo "alias hazel='source ~/Downloads/hazel-cli/venv/bin/activate && python3 ~/Downloads/hazel-cli/run.py'" >> ~/.zshrc
source ~/.zshrc
```

> Change `~/Downloads/hazel-cli` to wherever you put the folder.

### Step 5 — Launch

```bash
hazel
```

You should see:

```
  ╔══════════════════════════════════════╗
  ║   🌿  Hazel CLI  v2.0.0              ║
  ║   AI-Powered Cybersecurity Terminal  ║
  ╚══════════════════════════════════════╝

  AI Provider : not set — run: set-api groq
```

---

## Getting API Keys (Free)

You only need **one** API key to use AI features. All options below are free.

---

### 🥇 Option 1 — Groq (Recommended)

**Why:** Fastest responses. Best free model (Llama 3.3 70B). 14,400 req/day free.

1. Go to **https://console.groq.com**
2. Sign up with Google or GitHub (free)
3. Click **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_`)

---

### Option 2 — Google Gemini

**Why:** Very reliable. Google's own infrastructure. 1,500 req/day free.

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key (starts with `AIza`)

---

### Option 3 — OpenRouter

**Why:** Access to many models including completely free ones (no credit card needed).

1. Go to **https://openrouter.ai**
2. Sign up → go to **Keys** section
3. Click **Create Key**
4. Copy the key (starts with `sk-or-`)

> Free models available: `mistralai/mistral-7b-instruct:free`

---

### Option 4 — Ollama (Local, No Internet)

**Why:** 100% private. Works offline. No API key needed.

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (do this once)
ollama pull llama3

# Ollama starts automatically — or run manually:
ollama serve
```

---

## Adding API Keys to Hazel

Once Hazel is running, add your key with:

```
[hazel] ~ ❯ set-api groq
```

You'll see:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔑  Set API Key — Groq (Llama3-70b)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Free tier: 14,400 req/day — completely free
  Get key  : https://console.groq.com
  Key hint : Starts with: gsk_
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Paste your groq API key (hidden):
```

The key is **hidden while you type** (like a password). After saving:

```
  ✓  Key saved: gsk_****abcd
  Stored in: /home/user/Downloads/hazel-cli/.env
```

### Add multiple providers:

```
[hazel] ~ ❯ set-api groq
[hazel] ~ ❯ set-api gemini
[hazel] ~ ❯ set-api openrouter
```

---

## Selecting AI Provider

```
[hazel] ~ ❯ ai-provider groq
  ✓  Active provider set to: Groq (Llama3-70b)

[hazel] ~ ❯ ai-provider gemini
  ✓  Active provider set to: Google Gemini

[hazel] ~ ❯ ai-provider openrouter
  ✓  Active provider set to: OpenRouter (Multi-model)

[hazel] ~ ❯ ai-provider ollama
  ✓  Active provider set to: Ollama (Local)
```

### Check provider status:

```
[hazel] ~ ❯ ai status
```

Output:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🤖  AI Provider Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Groq (Llama3-70b)  ← ACTIVE
  Status : ✓ configured
  Key    : gsk_****abcd
  Free   : 14,400 req/day — completely free

  Google Gemini
  Status : ✓ configured
  Key    : AIza****8HcA
  Free   : 15 req/min, 1500/day — free tier

  OpenRouter (Multi-model)
  Status : ✗ no key
  Key    : run: set-api openrouter

  Ollama (Local — no key needed)
  Status : local
  Key    : no key needed
```

---

## All Commands

### 🤖 AI Commands

| Command | Description |
|---|---|
| `ask <question>` | Free-form AI cybersecurity Q&A |
| `ai explain <command>` | AI-powered deep command explanation |
| `ai suggest` | AI analyzes your session and suggests next steps |
| `ai writeup` | AI generates a professional pentest narrative |
| `ai status` | Show all providers and their status |

### 🔑 API Key Management

| Command | Description |
|---|---|
| `set-api groq` | Add Groq API key |
| `set-api gemini` | Add Google Gemini API key |
| `set-api openrouter` | Add OpenRouter API key |
| `set-api ollama` | Setup instructions for local Ollama |
| `ai-provider <name>` | Switch active AI provider |

### 🛠️ Built-in Tools

| Command | Description |
|---|---|
| `explain <cmd> [flags]` | Rule-based command & flag explainer |
| `writeup` | Print session writeup to terminal |
| `writeup save` | Save session writeup as `.md` file |
| `history` | Show last 20 commands |
| `history search <keyword>` | Search command history |
| `hazel freq` | Show most frequently used commands |
| `hazel help` | Show full command reference |
| `exit` / `quit` | Exit Hazel |

---

## AI Commands Demo

### Ask a question

```
[hazel] ~ ❯ ask how do I enumerate SMB shares on 10.10.10.1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🤖  HAZEL AI  [groq]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Suggestion: Enumerate SMB shares using smbclient
  Reason: Lists all available shares without authentication
  Risk: Low risk — read-only enumeration

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🤖  AI Suggested Commands
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [1] smbclient -L //10.10.10.1 -N

  Run smbclient -L //10.10.10.1 -N ? [y/N]: y
```

---

### AI explain a command

```
[hazel] ~ ❯ ai explain nmap -sS -sV -A -p- 10.10.10.1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🤖  HAZEL AI  [groq]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  This command performs a comprehensive nmap scan:

  -sS  SYN scan (stealth) — sends SYN packets, doesn't
       complete TCP handshake, harder to log
  -sV  Version detection — probes open ports for service
       versions (e.g. Apache 2.4.38)
  -A   Aggressive — enables OS detection, version scan,
       script scan, and traceroute all at once
  -p-  Scan ALL 65535 ports (default only scans top 1000)

  Expected output: Open ports with service names and
  versions, OS guess, NSE script results.

  Risk: Noisy — easily detected by IDS/firewall.
  Only scan systems you have permission to test.
```

---

### AI suggest next steps

```
[hazel] ~ ❯ nmap -sS -sV 10.10.10.1
  [nmap output showing ports 22, 80, 3306 open]

  💡 HAZEL SUGGESTS:
  [1] HTTP on port 80 → gobuster dir -u http://10.10.10.1 -w common.txt
  [2] SSH on port 22  → hydra -L users.txt -P rockyou.txt 10.10.10.1 ssh

[hazel] ~ ❯ ai suggest

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🤖  HAZEL AI  [groq]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Based on your session, you've found ports 22, 80, 3306.
  Here are your next steps:

  1. Enumerate the web server for hidden directories
  2. Check MySQL for default credentials
  3. Try to identify the web framework running

  <cmd>gobuster dir -u http://10.10.10.1 -w /usr/share/wordlists/dirb/common.txt -x php,html</cmd>
  <cmd>mysql -h 10.10.10.1 -u root -p</cmd>
  <cmd>whatweb http://10.10.10.1</cmd>
```

---

### Generate writeup

```
[hazel] ~ ❯ ai writeup

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📝  AI WRITEUP  [groq]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Executive Summary
  The assessment of 10.10.10.1 identified three open services
  including an exposed MySQL database and Apache web server.

  Methodology
  Phase 1 - Reconnaissance: Network scanning with nmap
  Phase 2 - Enumeration: Web directory brute-force with gobuster
  Phase 3 - Exploitation: SQL injection testing with sqlmap

  Findings
  - Port 80: Apache 2.4.38 — directory traversal possible
  - Port 3306: MySQL 5.7 — default credentials accepted
  - /admin panel accessible without authentication

  Recommendations
  - Disable default MySQL root password
  - Implement web application firewall
  - Restrict database access to localhost only

  Save as .md file? [y/N]:
```

---

## Safety System

All AI-suggested commands go through Hazel's full safety pipeline:

```
AI generates command
        ↓
  Hazel shows it to you
        ↓
  You confirm (y/N)
        ↓
  Typo check (analyzer.py)
        ↓
  Danger check (security.py)
        ↓
  Execute
```

**AI can never run commands directly.** Every suggested command requires your explicit confirmation. Even after you confirm, Hazel still checks for dangerous patterns.

### Commands Hazel will warn about:

| Command | Risk Level |
|---|---|
| `rm -rf /` | CRITICAL — blocks by default |
| `rm -rf ~` | CRITICAL — blocks by default |
| `chmod 777 *` | HIGH — requires confirmation |
| `dd if=... of=/dev/...` | CRITICAL — blocks by default |
| `curl URL \| sh` | HIGH — requires confirmation |
| Fork bombs `:(){:\|:&};:` | CRITICAL — blocks by default |

---

## Troubleshooting

### `source: no such file or directory: venv/bin/activate`
The venv path is wrong in your alias. Fix:
```bash
sed -i '/alias hazel/d' ~/.zshrc
echo "alias hazel='source ~/Downloads/hazel-cli/venv/bin/activate && python3 ~/Downloads/hazel-cli/run.py'" >> ~/.zshrc
source ~/.zshrc
```

### `No module named 'prompt_toolkit'`
```bash
cd ~/Downloads/hazel-cli
source venv/bin/activate
pip install prompt_toolkit
```

### `Gemini API error 404: models/gemini-1.5-flash not found`
Update `providers/gemini.py` — change model to `gemini-2.0-flash`.

### `Groq API error 404: model not found`
Update `providers/groq.py` — change model to `llama-3.3-70b-versatile`. Hazel now auto-tries fallback models.

### `OpenRouter: No endpoints found for llama-3-8b-instruct:free`
Update `providers/openrouter.py` — change model to `mistralai/mistral-7b-instruct:free`.

### `Ollama not reachable at localhost:11434`
```bash
# Install Ollama first
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3
ollama serve
```

### AI not responding / all providers failing
Check `ai status` to see which keys are configured:
```
[hazel] ~ ❯ ai status
```
If no providers are configured, run `set-api groq` and get a free key from https://console.groq.com.

---

## Security Notes

- **Never commit `.env`** — it contains your API keys. It's in `.gitignore` by default.
- API keys are stored in `.env` with `chmod 600` (only you can read it).
- Keys are **never printed in full** — always masked like `gsk_****abcd`.
- AI features are **optional** — Hazel works fully without any API key.

---

## Tech Stack

| Component | Technology |
|---|---|
| Terminal UI | `prompt_toolkit` |
| AI providers | Pure `urllib` — no SDK needed |
| Command history | `sqlite3` (stdlib) |
| Typo correction | `difflib` (stdlib) |
| Key storage | `.env` file with `chmod 600` |
| Execution | `subprocess` + `os.system` |

**Zero heavyweight dependencies.** Only `prompt_toolkit` needs installing.

---

## License

MIT — free for personal and commercial use.

---

*Built with 🌿 by Hazel CLI*
