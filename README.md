# Competition Tracker v2

**Multi-Domain Intelligence & Email Distribution Platform**

Curated news intelligence and job updates, delivered automatically on schedule. This production-grade Python system ingests RSS feeds, filters and deduplicates high-signal stories, and distributes clean HTML digests to targeted recipients—without mixing audiences.

**Repository:** [github.com/habinrahman/competition-tracker](https://github.com/habinrahman/competition-tracker)

---

## Overview

Staying current across EdTech, Cloud & DevOps, and GenAI is demanding. **Competition Tracker v2** automates curated insights and a **weekly MicroDegree newsletter** (jobs + tech intelligence), delivered straight to subscribers’ inboxes with token-based unsubscribe support.

### Why it matters

- One codebase serving multiple domains  
- Predictable, automated operations  
- Secure, environment-driven configuration  
- Cron-ready deployment on DigitalOcean  

---

## Key Features

| Area | Description |
|------|-------------|
| **Multi-domain pipelines** | EdTech (India), Cloud & DevOps (AWS, Azure, GCP, K8s, infra), GenAI (LLMs, tools, APIs) |
| **Weekly MicroDegree newsletter** | Six jobs + 15 blended GenAI/Cloud stories; one send per week via `tech@mdegree.in` |
| **Email distribution** | Gmail-friendly HTML; domain-specific routing; mass newsletters via SES |
| **Unsubscribe** | HMAC token links aligned with subscriber management |
| **RSS intelligence** | Google News RSS and time-bounded fetches |
| **Optional AI filtering** | OpenAI-assisted filtering with fail-open behavior |
| **Deduplication** | Groups similar stories and merges sources |
| **Automation** | Cron on DigitalOcean |
| **Observability** | Per-domain structured logs (`logs/`) |

---

## Architecture

```text
Google News RSS / Portal API
        │
        ▼
     Fetcher
        │
        ▼
  Filtering (rules / optional AI)
        │
        ▼
   Deduplication
        │
        ▼
    HTML builder
        │
        ▼
   Email (SMTP / mass sender)
        │
        ▼
    Subscribers (Sheet / env)
        │
        ▼
  Cron jobs (DigitalOcean)
```

---

## Project Structure

```text
competition-tracker-v2/
├── common/                 # Shared utilities (emailer, fetcher, subscribers, mass_sender, …)
├── domains/
│   ├── edtech/
│   ├── cloud_devops/
│   └── genai/
├── jobs/                   # Job scraper + job digest HTML
├── runners/                # Python entrypoints (newsletters, mass sends, job digest)
├── scripts/                # Cron-friendly shell wrappers
├── server/                 # Unsubscribe API (optional)
├── logs/                   # Runtime logs
├── requirements.txt
├── .env                    # Local only (not committed)
└── README.md
```

---

## Installation Guide

### 1. Clone the repository

```bash
git clone https://github.com/habinrahman/competition-tracker.git
cd competition-tracker-v2
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate:

**Linux / macOS**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Place Google Sheets credentials (e.g. `credentials.json`) in the project root if you use `common.subscribers` for mass lists.

---

## Environment Variables

Create a `.env` file in the project root. Example (use your own values—**never commit** `.env`):

```env
# Per-newsletter SMTP recipients (single-send runners)
EDTECH_RECIPIENTS=edtech@example.com
CLOUD_RECIPIENTS=cloud@example.com
GENAI_RECIPIENTS=genai@example.com

# Gmail SMTP (domain runners / dev / weekly preview)
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
PREVIEW_EMAIL=your_email@gmail.com

OPENAI_API_KEY=your_openai_api_key

DEV_MODE=false
DEV_EMAIL=your_email@example.com

UNSUBSCRIBE_BASE_URL=https://newsletter.mddegree.in
UNSUBSCRIBE_SECRET=your_hmac_secret

# Optional: override job API (default: portal public jobs JSON)
# JOBS_API_URL=https://portal.microdegree.work/api/external-jobs/public
```

Mass sends use **Amazon SES** credentials configured in `common/mass_sender.py` (or override via `SES_SMTP_HOST` / `SES_SMTP_PORT` where supported).

**Preview before mass send:** run `python runners/run_weekly_preview.py` locally. It builds the same weekly HTML and sends one copy to `PREVIEW_EMAIL` via Gmail (`SMTP_EMAIL` / `SMTP_PASSWORD`). Subject is prefixed with `[PREVIEW]`. Does not touch subscribers or the production lock file.

---

## Running the System

```bash
python runners/run_edtech.py
python runners/run_cloud.py
python runners/run_genai.py
python runners/run_mass_weekly.py
python runners/run_weekly_preview.py
```

---

## Cron Schedule (IST)

All times below are **India Standard Time (IST)**.

| Day | Time (IST) | Script | Purpose |
|-----|------------|--------|---------|
| Monday | 8:30 AM | `run_cloud.py` | Founder Cloud intelligence (Gmail) |
| Monday | 8:45 AM | `run_edtech.py` | Founder EdTech intelligence (Gmail) |
| Monday | 9:00 PM | `run_mass_weekly.py` | **MicroDegree Weekly** — jobs + tech news (SES) |
| Friday | 8:30 AM | `run_genai.py` | Founder GenAI intelligence (Gmail) |

### Fix cron running at the wrong time (e.g. 2 PM instead of 8:30 AM)

If jobs fire ~5½ hours late, the server is using **UTC**. On the droplet:

```bash
timedatectl set-timezone Asia/Kolkata
timedatectl
```

Then install the IST crontab (template: `scripts/crontab.ist.example`):

```bash
cd /root/competition-tracker-v2
crontab scripts/crontab.ist.example
crontab -l
```

The first line must be `TZ=Asia/Kolkata`. Save a backup: `crontab -l > cron_backup.txt`.

---

## Deployment on DigitalOcean

1. **Droplet:** Ubuntu LTS, Python 3.x, `git`, and a virtualenv under the app path (e.g. `/root/competition-tracker-v2`).  
2. **Secrets:** Copy `.env`, `credentials.json` (if used), and any TLS/SMTP configuration securely; restrict file permissions.  
3. **Cron:** Install entries under the app user; use absolute paths to `venv/bin/python` and append logs under `logs/`.  
4. **Time zone:** `timedatectl set-timezone Asia/Kolkata` and `TZ=Asia/Kolkata` at the top of crontab (see `scripts/crontab.ist.example`).  
5. **Unsubscribe:** Run the FastAPI unsubscribe service (`server/`) behind a process manager if you host the public unsubscribe URL separately.  

---

## Example Email Outputs

- **MicroDegree Weekly:** Six job cards, 15 blended GenAI/Cloud stories, preheader, and one unsubscribe link.  
- **Founder digests:** Domain-specific intelligence via Gmail (unchanged).  

To add screenshots:

```bash
mkdir screenshots
```

Then in this README:

```markdown
![Newsletter](screenshots/newsletter.png)
![Job digest](screenshots/jobs_digest.png)
```

---

## Tech Stack

| Category | Technologies |
|----------|----------------|
| Language | Python 3 |
| HTTP / parsing | `requests`, BeautifulSoup |
| AI | OpenAI API (optional) |
| Email | SMTP (Gmail), Amazon SES (mass) |
| Sheets | `gspread`, OAuth2 service account |
| Scheduling | Cron |
| Hosting | DigitalOcean |
| Version control | Git, GitHub |

---

## Release Information (v2.0)

- **Version:** v2.0  
- **Status:** Production-ready  

Tagging example:

```bash
git tag -a v2.0 -m "Competition Tracker v2 - Production Release"
git push origin v2.0
```

---

## Author Information

**Habin Rahman**

- Email: [habin936@gmail.com](mailto:habin936@gmail.com)  
- GitHub: [github.com/habinrahman](https://github.com/habinrahman)  

---

## License

This project is licensed under the **MIT License**.

---

## Support and Contributions

If this project is useful to you:

- Star the repository  
- Fork and open pull requests for improvements  
- Share with others building similar automation  

For bugs or feature ideas, use GitHub **Issues** on the repository.
