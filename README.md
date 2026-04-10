# Competition Tracker v2

**Multi-Domain Intelligence & Email Distribution Platform**

Curated news intelligence and job updates, delivered automatically on schedule. This production-grade Python system ingests RSS feeds, filters and deduplicates high-signal stories, and distributes clean HTML digests to targeted recipients—without mixing audiences.

**Repository:** [github.com/habinrahman/competition-tracker](https://github.com/habinrahman/competition-tracker)

---

## Overview

Staying current across EdTech, Cloud & DevOps, and GenAI is demanding. **Competition Tracker v2** automates curated insights and a **weekly MicroDegree job digest**, delivered straight to subscribers’ inboxes with token-based unsubscribe support.

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
| **Weekly job digest** | Latest roles from the MicroDegree hiring portal; mass send via `tech@mdegree.in` |
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

# Gmail SMTP (domain runners / dev)
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password

OPENAI_API_KEY=your_openai_api_key

DEV_MODE=false
DEV_EMAIL=your_email@example.com

UNSUBSCRIBE_BASE_URL=https://newsletter.mddegree.in
UNSUBSCRIBE_SECRET=your_hmac_secret

# Optional: override job API (default: portal public jobs JSON)
# JOBS_API_URL=https://portal.microdegree.work/api/external-jobs/public
```

Mass sends use **Amazon SES** credentials configured in `common/mass_sender.py` (or override via `SES_SMTP_HOST` / `SES_SMTP_PORT` where supported).

---

## Running the System

```bash
python runners/run_edtech.py
python runners/run_cloud.py
python runners/run_genai.py
python runners/run_jobs_digest.py
python runners/run_mass_cloud.py
python runners/run_mass_genai.py
```

---

## Cron Schedule (IST)

| Day | Time | Script | Purpose |
|-----|------|--------|---------|
| Monday | 8:30 AM | `run_cloud.py` | Cloud intelligence |
| Monday | 8:45 AM | `run_edtech.py` | EdTech intelligence |
| Monday | 9:00 AM | `run_mass_cloud.py` | Mass cloud newsletter |
| Wednesday | 9:00 AM | `run_jobs_digest.py` | Weekly job digest |
| Friday | 8:30 AM | `run_genai.py` | GenAI intelligence |
| Friday | 9:00 AM | `run_mass_genai.py` | Mass GenAI newsletter |

Example (job digest, Wednesday 09:00 IST—set `TZ=Asia/Kolkata` in crontab):

```bash
0 9 * * 3 cd /root/competition-tracker-v2 && /root/competition-tracker-v2/venv/bin/python runners/run_jobs_digest.py >> logs/jobs.log 2>&1
```

---

## Deployment on DigitalOcean

1. **Droplet:** Ubuntu LTS, Python 3.x, `git`, and a virtualenv under the app path (e.g. `/root/competition-tracker-v2`).  
2. **Secrets:** Copy `.env`, `credentials.json` (if used), and any TLS/SMTP configuration securely; restrict file permissions.  
3. **Cron:** Install entries under the app user; use absolute paths to `venv/bin/python` and append logs under `logs/`.  
4. **Time zone:** `crontab -e` → `TZ=Asia/Kolkata` for IST schedules.  
5. **Unsubscribe:** Run the FastAPI unsubscribe service (`server/`) behind a process manager if you host the public unsubscribe URL separately.  

---

## Example Email Outputs

- **Newsletter digest:** Multi-story cards with optional hero images, source lines, and read links.  
- **Job digest:** Up to six roles with apply links, portal CTA, and per-recipient unsubscribe footer.  

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
