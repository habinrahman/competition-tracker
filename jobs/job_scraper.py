from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup

from common.logger import get_logger

logger = get_logger("jobs")

JOBS_URL = "https://portal.microdegree.work/jobs"
# Public JSON feed (the /jobs page is a SPA; listings are loaded from this API).
JOBS_API_URL = os.getenv(
    "JOBS_API_URL",
    "https://portal.microdegree.work/api/external-jobs/public",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
}


def _parse_created_at(raw: str | None) -> datetime:
    if not raw:
        return datetime.min.replace(tzinfo=timezone.utc)
    text = str(raw).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def _normalize_job_row(row: dict[str, Any], fallback_link: str) -> dict[str, str] | None:
    title = (row.get("job_role") or row.get("title") or "").strip()
    if not title:
        return None
    company = (row.get("company") or "").strip() or "Not specified"
    location = (row.get("location") or "").strip() or "Not specified"
    exp = row.get("experience")
    experience = (str(exp).strip() if exp is not None else "") or "Not specified"
    link = (row.get("apply_link") or row.get("link") or "").strip() or fallback_link
    return {
        "title": title,
        "company": company,
        "location": location,
        "experience": experience,
        "link": link,
        "_sort": _parse_created_at(row.get("created_at")),
    }


def _fetch_jobs_from_api(limit: int) -> list[dict[str, str]]:
    jobs_out: list[dict[str, str]] = []
    try:
        response = requests.get(
            JOBS_API_URL,
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as e:
        logger.error("[JOBS ERROR] API request failed: %s", e)
        return jobs_out
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error("[JOBS ERROR] Invalid API JSON: %s", e)
        return jobs_out

    if not isinstance(payload, dict) or not payload.get("success"):
        logger.warning("[JOBS] API response missing success flag or wrong shape.")
        return jobs_out

    raw_jobs = payload.get("jobs") or []
    if not isinstance(raw_jobs, list):
        return jobs_out

    parsed: list[dict[str, str]] = []
    for row in raw_jobs:
        if not isinstance(row, dict):
            continue
        norm = _normalize_job_row(row, JOBS_URL)
        if norm:
            parsed.append(norm)

    parsed.sort(key=lambda j: j["_sort"], reverse=True)

    for item in parsed[:limit]:
        jobs_out.append(
            {
                "title": item["title"],
                "company": item["company"],
                "location": item["location"],
                "experience": item["experience"],
                "link": item["link"],
            }
        )
    return jobs_out


def _fetch_jobs_from_html(limit: int) -> list[dict[str, str]]:
    """Fallback if the portal ever serves SSR HTML again."""
    jobs: list[dict[str, str]] = []
    try:
        response = requests.get(JOBS_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("[JOBS ERROR] Failed to fetch jobs page: %s", e)
        return jobs

    soup = BeautifulSoup(response.text, "html.parser")
    job_cards = soup.select("div.rounded-xl, div.shadow-md, div.border")

    for card in job_cards:
        if len(jobs) >= limit:
            break
        try:
            title_tag = card.find(["h2", "h3"])
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            text_content = card.get_text(" ", strip=True)

            company = "Not specified"
            location = "Not specified"
            experience = "Not specified"

            lines = text_content.split("  ")

            for line in lines:
                if "Experience" in line:
                    experience = line.replace("Experience:", "").strip()
                elif "Bangalore" in line or "India" in line:
                    location = line.strip()
                elif line != title and len(line) < 60:
                    company = line.strip()

            jobs.append(
                {
                    "title": title,
                    "company": company,
                    "location": location,
                    "experience": experience,
                    "link": JOBS_URL,
                }
            )

        except Exception as e:
            logger.warning("[JOBS PARSE ERROR] %s", e)
            continue

    return jobs


def fetch_latest_jobs(limit: int = 6) -> list[dict[str, str]]:
    """Fetch the latest job postings from the MicroDegree portal (API-first, HTML fallback)."""
    jobs = _fetch_jobs_from_api(limit)
    if not jobs:
        logger.info("[JOBS] API returned no jobs; trying HTML fallback.")
        jobs = _fetch_jobs_from_html(limit)

    logger.info("[JOBS] Fetched %d latest jobs.", len(jobs))
    return jobs
