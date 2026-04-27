from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx
import trafilatura

from .models import ArticleContent

log = logging.getLogger(__name__)

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)

SKIP_HOSTS = frozenset({
    "reddit.com", "www.reddit.com", "old.reddit.com", "i.reddit.com",
    "redd.it", "v.redd.it", "i.redd.it",
    "imgur.com", "i.imgur.com",
    "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    "twitter.com", "x.com", "mobile.twitter.com",
})

MAX_CHARS = 8000
FETCH_TIMEOUT = 10.0


def _should_skip(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return True
    return host in SKIP_HOSTS


async def fetch_article(
    url: str, client: httpx.AsyncClient
) -> ArticleContent | None:
    if not url or _should_skip(url):
        return None
    try:
        resp = await client.get(
            url,
            follow_redirects=True,
            timeout=FETCH_TIMEOUT,
            headers={"User-Agent": BROWSER_USER_AGENT},
        )
        resp.raise_for_status()
        html, final_url = resp.text, str(resp.url)
    except httpx.HTTPError as exc:
        log.debug("fetch_article HTTP failure for %s: %s", url, exc)
        return None

    try:
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
    except Exception as exc:
        log.debug("trafilatura.extract failed for %s: %s", url, exc)
        return None

    if not text or not text.strip():
        return None

    title: str | None = None
    try:
        meta = trafilatura.extract_metadata(html)
        if meta is not None:
            title = meta.title
    except Exception:
        title = None

    return ArticleContent(url=final_url, title=title, content=text[:MAX_CHARS])
