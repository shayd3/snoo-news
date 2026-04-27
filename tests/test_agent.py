from __future__ import annotations

import pytest
from pydantic_ai import capture_run_messages
from pydantic_ai.models.test import TestModel

from snoo_news.agent import TARGET_SUBREDDITS, agent, run_digest
from snoo_news.models import ArticleContent, Digest, RedditPost
from snoo_news.reddit import RedditClient


class StubRedditClient(RedditClient):
    """RedditClient that returns canned posts without hitting the network."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []
        self.article_calls: list[str] = []

    async def fetch_article(self, url: str) -> ArticleContent | None:
        self.article_calls.append(url)
        if "/story" in url:
            return ArticleContent(
                url=url, title="Stub", content="Stub article body."
            )
        return None

    async def fetch_hot(self, subreddit: str, limit: int = 10) -> list[RedditPost]:
        self.calls.append((subreddit, limit))
        return [
            RedditPost(
                subreddit=subreddit,
                title=f"[{subreddit}] Top story",
                url=f"https://example.com/{subreddit}/story",
                permalink=f"https://www.reddit.com/r/{subreddit}/comments/x/top_story/",
                score=1000,
                num_comments=100,
            ),
            RedditPost(
                subreddit=subreddit,
                title=f"[{subreddit}] Second story",
                url=f"https://example.com/{subreddit}/two",
                permalink=f"https://www.reddit.com/r/{subreddit}/comments/y/second/",
                score=500,
                num_comments=50,
            ),
        ]

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_agent_calls_tool_and_returns_digest():
    stub = StubRedditClient()
    with agent.override(model=TestModel()):
        with capture_run_messages() as messages:
            result = await agent.run(
                "Build today's news digest from the four target subreddits.",
                deps=stub,
            )

    assert isinstance(result.output, Digest)

    tool_call_subs = {
        part.args.get("subreddit") if isinstance(part.args, dict) else None
        for msg in messages
        for part in getattr(msg, "parts", [])
        if getattr(part, "part_kind", "") == "tool-call"
        and getattr(part, "tool_name", "") == "get_hot_posts"
    }
    # TestModel should have invoked the tool at least once.
    assert tool_call_subs, "TestModel did not invoke get_hot_posts"

    tool_names = {
        getattr(part, "tool_name", "")
        for msg in messages
        for part in getattr(msg, "parts", [])
        if getattr(part, "part_kind", "") == "tool-call"
    }
    assert "get_article" in tool_names, "TestModel did not invoke get_article"


@pytest.mark.asyncio
async def test_run_digest_helper_uses_overridden_model():
    stub = StubRedditClient()
    with agent.override(model=TestModel()):
        digest = await run_digest(stub)
    assert isinstance(digest, Digest)


def test_target_subreddits_match_agent_config():
    assert TARGET_SUBREDDITS == ("news", "tech")
