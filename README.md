Competition Tracker v2
Multi-Domain Intelligence & Email Distribution Platform

Curated news intelligence and job updates, delivered automatically on schedule. This production-grade Python system ingests RSS feeds, filters and deduplicates high-signal stories, and distributes clean HTML digests to targeted recipients—without mixing audiences.

🔗 GitHub Repository:
https://github.com/habinrahman/competition-tracker

📌 Overview

Staying updated across EdTech, Cloud & DevOps, and GenAI can be overwhelming. Competition Tracker v2 automates the process by delivering curated insights and weekly job digests directly to stakeholders' inboxes.

💡 Why It Matters
One codebase serving multiple domains
Predictable and automated operations
Secure, environment-driven email routing
Cron-ready deployment on DigitalOcean
✨ Key Features
📊 Multi-Domain Intelligence Pipelines
EdTech: India ecosystem insights
Cloud & DevOps: AWS, Azure, GCP, Kubernetes, and infrastructure
GenAI: LLMs, frameworks, APIs, and tools
💼 Weekly MicroDegree Job Digest
Fetches the latest jobs from the MicroDegree Hiring Portal
Sends curated opportunities to subscribers
📧 Automated Email Distribution
Gmail-compatible responsive HTML templates
Domain-specific recipient routing
Mass email automation via tech@mdegree.in
🔐 Secure Unsubscribe System
Token-based unsubscribe links
Privacy-focused and compliant
🔎 RSS-Based Intelligence
Google News RSS ingestion
Time-bounded queries for recent insights
🧠 Optional AI Filtering
LLM-based filtering using OpenAI
Fail-open design for reliability
🔁 Deduplication & Content Merging
Groups similar stories
Aggregates multiple sources
⏰ Cron-Based Automation
Fully automated scheduling on DigitalOcean
📊 Observability & Logging
Structured logs per domain
Production-ready monitoring
🏗️ Architecture
Google News RSS
        │
        ▼
     Fetcher
        │
        ▼
     Filtering (Rules/AI)
        │
        ▼
     Deduplication
        │
        ▼
     HTML Builder
        │
        ▼
     Email Sender
        │
        ▼
     Subscribers
        │
        ▼
   Cron Jobs (DigitalOcean)
📁 Project Structure
competition-tracker/
│
├── common/                 # Shared utilities
├── domains/
│   ├── edtech/
│   ├── cloud_devops/
│   └── genai/
├── jobs/                   # MicroDegree job digest modules
├── runners/                # Execution scripts
├── scripts/                # Cron-safe shell wrappers
├── server/                 # Unsubscribe service
├── logs/                   # Runtime logs
├── requirements.txt
├── .gitignore
└── README.md
⚙️ Installation
1️⃣ Clone the Repository
git clone https://github.com/habinrahman/competition-tracker.git
cd competition-tracker
2️⃣ Create a Virtual Environment
python -m venv venv

Activate the environment:

Linux/macOS
source venv/bin/activate
Windows
venv\Scripts\activate
3️⃣ Install Dependencies
pip install -r requirements.txt
🔐 Environment Variables

Create a .env file in the project root:

EDTECH_RECIPIENTS=edtech@example.com
CLOUD_RECIPIENTS=cloud@example.com
GENAI_RECIPIENTS=genai@example.com

SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password

OPENAI_API_KEY=your_openai_api_key

DEV_MODE=false
DEV_EMAIL=your_email@example.com

UNSUBSCRIBE_BASE_URL=https://newsletter.mddegree.in

⚠️ Never commit this file to GitHub.

▶️ Running the System
python runners/run_edtech.py
python runners/run_cloud.py
python runners/run_genai.py
python runners/run_jobs_digest.py
python runners/run_mass_cloud.py
python runners/run_mass_genai.py
⏰ Cron Schedule (IST)
Day	Time	Script	Purpose
Monday	8:30 AM	run_cloud.py	Cloud Intelligence
Monday	8:45 AM	run_edtech.py	EdTech Intelligence
Monday	9:00 AM	run_mass_cloud.py	Mass Cloud Newsletter
Wednesday	9:00 AM	run_jobs_digest.py	Weekly Job Digest
Friday	8:30 AM	run_genai.py	GenAI Intelligence
Friday	9:00 AM	run_mass_genai.py	Mass GenAI Newsletter

Example cron entry:

0 9 * * 3 cd /root/competition-tracker-v2 && /root/competition-tracker-v2/venv/bin/python runners/run_jobs_digest.py >> logs/jobs.log 2>&1
📧 Example Email Outputs
📬 Newsletter Digest

Add screenshots here

💼 Job Digest

Add screenshots here

To add screenshots:

mkdir screenshots

Then reference them in the README:

![Newsletter](screenshots/newsletter.png)
![Job Digest](screenshots/jobs_digest.png)
🛠️ Tech Stack
Category	Technologies
Language	Python
Web Scraping	Requests, BeautifulSoup
AI Integration	OpenAI API
Email Automation	SMTP
Scheduling	Cron
Deployment	DigitalOcean
Version Control	Git & GitHub
🚀 Release

Version: v2.0
Status: Production Ready

git tag -a v2.0 -m "Competition Tracker v2 - Production Release"
git push origin v2.0
👨‍💻 Author

Habin Rahman
📧 habin936@gmail.com

🔗 https://github.com/habinrahman

📜 License

This project is licensed under the MIT License.

⭐ Support

If you find this project useful:

⭐ Star the repository
🍴 Fork it
📢 Share it with others
