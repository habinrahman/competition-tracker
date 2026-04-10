from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

CONNECT_TIMEOUT = 3
READ_TIMEOUT = 6
REQUEST_TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)

_image_cache: dict[str, str | None] = {}


def is_valid_image(url: str) -> bool:
    if not url:
        return False

    url = url.lower()

    # must be http
    if not url.startswith("http"):
        return False

    # block unwanted types
    blocked_keywords = [
        "logo", "icon", "avatar", "profile", "user",
        "ads", "banner", "sprite", "emoji", "badge",
    ]

    if any(k in url for k in blocked_keywords):
        return False

    # block svg
    if ".svg" in url:
        return False

    # allow images even without extension (CDNs)
    valid_ext = [".jpg", ".jpeg", ".png", ".webp"]

    if not any(ext in url for ext in valid_ext):
        # allow if from CDN or contains "image"
        if "image" not in url and "media" not in url:
            return False

    return True


def _normalize_img_url(raw: str, page_url: str) -> str:
    img = (raw or "").strip()
    if not img:
        return ""
    if img.startswith("//"):
        img = "https:" + img
    elif img.startswith("/"):
        img = urljoin(page_url, img)
    elif not img.startswith("http"):
        img = urljoin(page_url, img)
    return img if img.startswith("http") else ""


def score_image(img_url: str, page_url: str, position: int) -> int:
    score = 0

    img = img_url.lower()
    try:
        parts = page_url.split("/")
        domain = parts[2] if len(parts) > 2 else ""
    except Exception:
        domain = ""
    domain = domain.lower()

    # SAME DOMAIN → VERY IMPORTANT
    if domain and domain in img:
        score += 10

    # good keywords
    if any(k in img for k in ["hero", "cover", "article", "header"]):
        score += 5

    # early images → likely hero
    if position < 3:
        score += 3

    # bad keywords
    if any(
        k in img
        for k in [
            "logo",
            "icon",
            "avatar",
            "profile",
            "ads",
            "banner",
        ]
    ):
        score -= 10

    return score


def extract_image(url: str) -> str | None:
    if url in _image_cache:
        return _image_cache[url]

    og = None
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        images: list[str] = []

        # OG image (candidate, not final)
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            images.append(str(og["content"]).strip())

        # All images inside main content
        main = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", {"role": "main"})
            or soup.body
        )
        if main is None:
            main = soup

        for tag in main.find_all("img"):
            src = (
                tag.get("src")
                or tag.get("data-src")
                or tag.get("data-lazy-src")
            )

            if not src:
                continue

            # skip small images
            width = tag.get("width")
            height = tag.get("height")

            if width and height:
                try:
                    w = int(str(width).replace("px", "").strip())
                    h = int(str(height).replace("px", "").strip())
                    if w < 200 or h < 200:
                        continue
                except Exception:
                    pass

            images.append(str(src).strip())

        normalized_images: list[str] = []
        for img in images:
            norm = _normalize_img_url(img, url)
            if norm:
                normalized_images.append(norm)

        best_img = None
        best_score = -999

        for idx, img in enumerate(normalized_images):

            if not is_valid_image(img):
                continue

            s = score_image(img, url, idx)

            if s > best_score:
                best_score = s
                best_img = img

        if best_img:
            logger.info(f"[IMG FOUND] {best_img}")
            _image_cache[url] = best_img
            return best_img

        # fallback to OG if valid
        if og and og.get("content"):
            og_img = _normalize_img_url(str(og["content"]), url)
            if og_img and is_valid_image(og_img):
                logger.info(f"[IMG FOUND] {og_img}")
                _image_cache[url] = og_img
                return og_img

        logger.info(f"[IMG NOT FOUND] {url}")

    except requests.exceptions.ConnectTimeout:
        logger.warning(f"[IMG TIMEOUT] Connection timeout for {url}")

    except requests.exceptions.ReadTimeout:
        logger.warning(f"[IMG TIMEOUT] Read timeout for {url}")

    except requests.exceptions.HTTPError as e:
        logger.warning(f"[IMG HTTP ERROR] {url} - {e}")

    except requests.exceptions.RequestException as e:
        logger.warning(f"[IMG REQUEST ERROR] {url} - {e}")

    except Exception as e:
        logger.exception(f"[IMG UNKNOWN ERROR] {url} - {e}")

        _image_cache[url] = None
        return None

    _image_cache[url] = None
    return None


def enrich_news_items_with_images(
    items: list[dict[str, Any]],
    *,
    max_workers: int = 5,
) -> None:
    """Attach ``image`` to each item when OG/thumbnail fetch succeeds (mutates list in place)."""
    if not items:
        return

    links_ordered: list[str] = []
    seen: set[str] = set()
    for it in items:
        lk = (it.get("link") or "").strip()
        if not lk or lk in seen:
            continue
        seen.add(lk)
        links_ordered.append(lk)

    link_to_image: dict[str, str | None] = {}

    def _fetch(link: str) -> tuple[str, str | None]:
        return link, extract_image(link)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_fetch, lk) for lk in links_ordered]
        for fut in as_completed(futures):
            link, img = fut.result()
            link_to_image[link] = img

    for it in items:
        lk = (it.get("link") or "").strip()
        img = link_to_image.get(lk)
        if img:
            it["image"] = img
