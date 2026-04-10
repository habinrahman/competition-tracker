from bs4 import BeautifulSoup
import requests


def fetch_article_metadata(url: str) -> dict:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=6, headers=headers)

        soup = BeautifulSoup(response.text, "html.parser")

        def get_meta(prop, attr="property"):
            tag = soup.find("meta", {attr: prop})
            return tag["content"] if tag and tag.get("content") else None

        title = get_meta("og:title") or (soup.title.string if soup.title else None)
        image = get_meta("og:image") or get_meta("twitter:image", "name")
        description = get_meta("og:description")

        return {
            "title": title,
            "image": image,
            "description": description
        }

    except Exception as e:
        print("[metadata_error]", e)
        return {}
