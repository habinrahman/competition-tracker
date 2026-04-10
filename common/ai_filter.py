from __future__ import annotations

import os
import re

from openai import OpenAI


_WEAK_TITLE_MARKERS = (
    "top 10",
    "top 5",
    "top ten",
    "five reasons",
    "ten reasons",
    "why you",
    "why we",
    "why it matters",
    "what you need to know",
    "opinion:",
    "editorial:",
    "podcast:",
    "how to ",
    "guide to ",
    " best ",
    " worst ",
    " explained",
    "everything you need",
    "you won't believe",
    "click here",
)

_STRONG_KEYWORDS = (
    "launch",
    "funding",
    "raises",
    "raised",
    "acquires",
    "acquired",
    "acquisition",
    "merger",
    "partners",
    "partnership",
    "security",
    "breach",
    "model",
    "release",
    "investment",
    "invests",
    "invest ",
    "ipo",
    "cloud",
    "infrastructure",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "gpu",
    "inference",
    "benchmark",
    "valuation",
    "series ",
    "seed ",
    "round",
    "deal",
    "llm",
    "gpt",
    "claude",
    "anthropic",
    "openai",
    "nvidia",
    "microsoft",
    "google",
    "meta",
    "apple",
    "amazon",
    "edtech",
    "education technology",
)


def is_strong_signal(title: str) -> bool:
    """
    Drop listicles, vague commentary, opinions; keep hard news / product / deals / infra.
    """
    t = (title or "").strip().lower()
    if len(t) < 12:
        return False
    if any(w in t for w in _WEAK_TITLE_MARKERS):
        return False
    if re.search(r"\btop\s+\d+\b", t):
        return False
    if any(k in t for k in _STRONG_KEYWORDS):
        return True
    if re.search(r"\b(ai|ml)\b", t):
        return True
    return False

def _get_client() -> OpenAI:
    # Create client lazily so imports don't crash in cron environments
    # where OPENAI_API_KEY might not be set.
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _ai_yes_no(prompt: str) -> bool:
    import os

    # SAFETY: if no API key → bypass AI completely
    if not os.getenv("OPENAI_API_KEY"):
        return True

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        answer = response.choices[0].message.content.strip().upper()
        return answer == "YES"

    except Exception as e:
        # Preserve existing fail-open behavior
        print("AI filter error:", e)
        return True

def _ai_filter_edtech(title: str) -> bool:
    # MUST preserve the existing EdTech prompt verbatim (behavioral compatibility).
    prompt = f"""
Determine if this article is relevant to the Indian EdTech ecosystem.

Include:
- EdTech startups
- education technology
- online learning platforms
- AI in education
- EdTech funding
- EdTech acquisitions

Exclude:
- general education news
- school events
- unrelated startup news
- government education policy not related to technology

Title: {title}

Reply ONLY YES or NO.
"""
    return _ai_yes_no(prompt)


def _ai_filter_cloud_devops(title: str) -> bool:
    prompt = f"""
Determine if this article is relevant to Cloud & DevOps technical updates.

Include:
- AWS service updates (launches, releases, new features)
- DevOps tools and workflows
- cloud infrastructure, platform engineering
- CI/CD
- Kubernetes and container orchestration

Exclude:
- generic business news
- earnings/stock/marketing announcements without technical substance
- unrelated programming articles

Title: {title}

Reply ONLY YES or NO.
"""
    return _ai_yes_no(prompt)


def _ai_filter_genai(title: str) -> bool:
    prompt = f"""
Determine if this article is STRICTLY relevant to GenAI / LLM technical intelligence.

INCLUDE (high-signal technical):
- model releases/updates (GPT, Claude, Gemini, Llama, Mistral, etc.)
- frameworks (LangChain, LlamaIndex, vLLM, etc.)
- APIs, SDKs, tooling for building LLM apps
- benchmarks, evals, performance comparisons
- research with real practical impact (methods, architectures, scaling, inference, alignment) with concrete results

EXCLUDE:
- generic AI news summaries
- business/marketing fluff
- policy/regulation/opinion pieces

Title: {title}

Reply ONLY YES or NO.
"""
    return _ai_yes_no(prompt)


def ai_filter(title: str, domain: str | None = None, summary: str = "") -> bool:
    """
    Multi-domain AI filter.

    Backwards compatible with the previous signature: ai_filter(title, summary="")
    - If the second positional argument isn't a known domain, treat it as summary.
    """
    # Back-compat: if someone calls ai_filter(title, summary="...")
    if domain is not None and domain not in {"edtech", "cloud_devops", "aws_devops", "genai"}:
        summary = str(domain)
        domain = "edtech"

    d = (domain or "edtech").strip().lower()
    if d == "aws_devops":
        d = "cloud_devops"

    # summary currently unused but kept to avoid breaking callers
    _ = summary

    if d == "edtech":
        return _ai_filter_edtech(title)
    if d == "cloud_devops":
        return _ai_filter_cloud_devops(title)
    if d == "genai":
        return _ai_filter_genai(title)

    # Unknown domain: fail-open (production-safe, avoids dropping everything).
    return True