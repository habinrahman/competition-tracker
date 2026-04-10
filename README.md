# Multi-Domain Intelligence & Email Distribution Platform

**Curated news intelligence, delivered on schedule.** A production-oriented Python system that ingests Google News RSS, filters and deduplicates stories per domain, tracks what you have already sent, and distributes clean HTML digests to the right recipients—without mixing audiences.

---

## Overview

Staying current across EdTech funding, cloud infrastructure, and GenAI releases means drowning in noise. This platform automates **high-signal curation**: each domain runs an isolated pipeline with its own query, filters, merge rules, state file, and recipient list. Outputs are **cron-friendly**, **idempotent across runs** (via persisted “seen” state), and **email-first** for operators and stakeholders who want a single daily or weekly brief—not another dashboard tab.

**Why it matters:** one codebase, three verticals; predictable operations; explicit env-based routing so EdTech mail never lands in GenAI inboxes.

---

## Features

- **Multi-domain pipelines** — EdTech (India ecosystem), Cloud & DevOps (AWS/Azure/GCP/K8s/infra), GenAI (models, frameworks, APIs)
- **RSS ingestion** — Google News search RSS with time-bounded queries (`when:7d` where applicable)
- **Layered filtering** — Rule-based keyword allow/block lists; EdTech optionally uses an LLM classifier (`OPENAI_API_KEY`) with fail-open behavior on errors
- **Deduplication & merge** — Similar titles grouped; multiple outlets shown under one story in email
- **Adaptive recall (GenAI)** — Strict pass first; relaxed keyword pass only when the strict pass returns fewer than five items (still gated by allow/block lists and link deduplication)
- **Per-domain state** — JSON-backed “seen” keys under each domain’s `data/` directory to avoid repeat sends
- **HTML email digests** — Consistent layout: headline, intro, per-story sources with “Read full article →” links (no raw URL spam)
- **Strict recipient routing** — Each runner requires its own `*_RECIPIENTS` env var (no silent fallback to a shared list)
- **Optional dev redirect** — `DEV_MODE=true` sends all mail to `DEV_EMAIL` for safe testing
- **Operations-ready** — Per-domain log files, shell wrappers for cron, suitable for VPS deployment (e.g. DigitalOcean)

---

## Architecture

### Multi-domain design

Each vertical lives under `domains/<name>/` with **config** (query, locale, subject prefix) and **tracker** (fetch → filter → optional cap → merge → state diff → email). Shared mechanics live in `common/` so behavior stays consistent without copy-paste.

### Pipeline flow (per run)

1. **Fetch** — `common/fetcher.py` pulls Google News RSS for the domain query; optional published-date window aligns with “last 7 days” where the tracker enforces it.
2. **Filter** — Domain-specific rules (basic keyword allow/block lists) + 7-day window.
3. **Dedup / merge** — `common/dedup.py` merges near-duplicate titles and aggregates sources.
4. **State** — Removed: each run includes the full last 7 days.
5. **Email** — `common/emailer.py` builds HTML and sends via SMTP; recipients come **only** from the runner’s env list (unless `DEV_MODE` is on).

### Modularity

| Layer | Role |
|--------|------|
| `common/` | Fetch, dedup, state, logging, AI filter, SMTP |
| `domains/*/` | Queries, filters, caps, subject/intro for that vertical |
| `runners/` | Load `.env`, resolve recipients, invoke `run()` |
| `scripts/` | Bash entrypoints for cron (venv + log redirection) |

---

## Project structure

```
competition-tracker/
├── common/                 # Shared library (fetcher, dedup, emailer, state, logger, AI filter)
├── domains/
│   ├── edtech/             # India EdTech + optional LLM filter
│   ├── cloud_devops/       # Multi-cloud & DevOps intelligence
│   └── genai/              # High-signal GenAI / LLM feed
├── runners/                # run_edtech.py, run_cloud.py, run_genai.py
├── scripts/                # Cron-safe .sh wrappers
├── logs/                   # Per-domain log files (created at runtime)
├── .env                    # Secrets & recipient lists (not committed)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone

```bash
git clone <your-repo-url>
cd competition-tracker
```

### 2. Virtual environment

```bash
python -m venv venv
source venv/bin/activate          # Linux / macOS
# or: venv\Scripts\activate     # Windows
```

### 3. Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment file

Create `.env` in the project root (see **Environment variables** below). Never commit real secrets.

### 5. First run

From the project root, with `venv` activated:

```bash
python runners/run_edtech.py
python runners/run_cloud.py
python runners/run_genai.py
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EDTECH_RECIPIENTS` | **Yes** (EdTech runner) | Comma-separated emails for EdTech digests only |
| `CLOUD_RECIPIENTS` | **Yes** (Cloud runner) | Comma-separated emails for Cloud & DevOps digests only |
| `GENAI_RECIPIENTS` | **Yes** (GenAI runner) | Comma-separated emails for GenAI digests only |
| `SMTP_EMAIL` | **Yes** (send) | Gmail (or other SMTP) sender address |
| `SMTP_PASSWORD` | **Yes** (send) | App password or SMTP secret (e.g. Gmail app password) |
| `OPENAI_API_KEY` | Optional | Enables EdTech LLM filter; omit or invalid key → filter fail-open |
| `DEV_MODE` | Optional | `true` / `1` / `yes` / `on` → redirect all sends to `DEV_EMAIL`; default off |
| `DEV_EMAIL` | Optional | Used when `DEV_MODE` is enabled (defined in `common/emailer.py`) |

**Example** (structure only—use your real values):

```env
EDTECH_RECIPIENTS=you@company.com,colleague@company.com
CLOUD_RECIPIENTS=platform@company.com
GENAI_RECIPIENTS=research@company.com
SMTP_EMAIL=your-sender@gmail.com
SMTP_PASSWORD=your-app-password
OPENAI_API_KEY=sk-...
DEV_MODE=false
```

---

## Running the system

All commands assume project root and activated venv.

```bash
python runners/run_edtech.py
python runners/run_cloud.py
python runners/run_genai.py
```

Runners **raise** if the matching `*_RECIPIENTS` variable is missing or parses to no addresses—this avoids accidental cross-domain sends.

**Reset “seen” state** (e.g. to re-send a digest during testing):

```bash
# No seen-state files are used anymore.
```

---

## Cron setup (production)

Use the provided scripts or inline cron entries. Adjust the repo path and Python path for your server (e.g. DigitalOcean droplet).

**Example** — weekday 08:30 UTC (edit paths):

```cron
30 8 * * 1-5 cd /opt/competition-tracker && /opt/competition-tracker/venv/bin/python runners/run_edtech.py >> logs/edtech.log 2>&1
35 8 * * 1-5 cd /opt/competition-tracker && /opt/competition-tracker/venv/bin/python runners/run_cloud.py >> logs/cloud.log 2>&1
40 8 * * 1-5 cd /opt/competition-tracker && /opt/competition-tracker/venv/bin/python runners/run_genai.py >> logs/genai.log 2>&1
```

The `scripts/*.sh` files wrap `cd`, `source venv/bin/activate`, and log redirection—update `cd /root/competition-tracker` to match your deploy path.

---

## Example email output

Each message is a **single HTML digest**:

- **Subject line** — Domain-specific prefix plus date (e.g. EdTech India, Cloud & DevOps, GenAI).
- **Body** — Branded heading and short intro, then numbered stories.
- **Stories** — One canonical title per cluster; under it, **Source:** lines and **Read full article →** links (styled, opens in a new tab).
- **Footer** — Generic “Automated Intelligence Report” line.

Cloud and GenAI reuse the same HTML builder as EdTech with custom **heading** and **intro** text so the layout stays consistent while the copy matches the vertical.

---

## Future improvements

- **Richer AI filtering** — Tune prompts per domain or add lightweight scoring instead of pure keyword gates  
- **Dashboard** — Historical runs, click-through, and volume trends  
- **Analytics** — Story overlap across domains, source diversity metrics  
- **Real-time alerts** — Webhook or instant notify for breaking model releases or infra incidents  
- **Source expansion** — Beyond Google News RSS (official blogs, GitHub releases, vendor status APIs)

---

## Author

**Habin Rahman**  
Email: [habin936@gmail.com](mailto:habin936@gmail.com)

---

## License

Add a `LICENSE` file if you open-source the repo (e.g. MIT). This README does not impose a license by itself.
