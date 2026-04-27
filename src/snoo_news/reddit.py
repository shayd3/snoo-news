from __future__ import annotations

import httpx

from .models import ArticleContent, RedditPost

REDDIT_BASE = "https://www.reddit.com"
DEFAULT_USER_AGENT = "snoo-news/0.1 (by /u/snoo-news-agent)"


class RedditClient:
    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._user_agent = user_agent
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": user_agent},
            timeout=timeout,
        )

    async def __aenter__(self) -> "RedditClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def fetch_hot(self, subreddit: str, limit: int = 10) -> list[RedditPost]:
        url = f"{REDDIT_BASE}/r/{subreddit}/hot.json"
        resp = await self._client.get(url, params={"limit": limit})
        resp.raise_for_status()
        payload = resp.json()
        children = payload.get("data", {}).get("children", [])

        posts: list[RedditPost] = []
        for child in children:
            data = child.get("data", {})
            if data.get("stickied") or data.get("over_18"):
                continue
            permalink = data.get("permalink", "")
            posts.append(
                RedditPost(
                    subreddit=data.get("subreddit", subreddit),
                    title=data.get("title", ""),
                    url=data.get("url", ""),
                    permalink=f"{REDDIT_BASE}{permalink}" if permalink else "",
                    score=int(data.get("score", 0)),
                    num_comments=int(data.get("num_comments", 0)),
                    selftext=data.get("selftext", "") or "",
                    is_self=bool(data.get("is_self", False)),
                    over_18=bool(data.get("over_18", False)),
                    stickied=bool(data.get("stickied", False)),
                )
            )
        return posts

    async def fetch_article(self, url: str) -> ArticleContent | None:
        from .article import fetch_article as _fetch_article
        return await _fetch_article(url, self._client)
