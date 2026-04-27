import httpx
import pytest
import respx

from snoo_news.reddit import REDDIT_BASE, RedditClient


@pytest.mark.asyncio
async def test_fetch_hot_parses_and_filters(news_hot_payload):
    with respx.mock(base_url=REDDIT_BASE, assert_all_called=True) as router:
        route = router.get("/r/news/hot.json").mock(
            return_value=httpx.Response(200, json=news_hot_payload),
        )
        async with RedditClient(user_agent="test-agent/1.0") as client:
            posts = await client.fetch_hot("news", limit=10)

    titles = [p.title for p in posts]
    assert "Daily Discussion Megathread" not in titles, "stickied posts must be filtered"
    assert all(not p.over_18 for p in posts), "NSFW posts must be filtered"
    assert "City council passes new transit plan after months of debate" in titles
    assert "Major weather system causes power outages across the region" in titles
    assert len(posts) == 2

    transit = next(p for p in posts if "transit" in p.title)
    assert transit.score == 5234
    assert transit.num_comments == 1289
    assert transit.url == "https://example.com/news/transit-plan"
    assert transit.permalink.startswith("https://www.reddit.com/r/news/comments/abc123")

    sent_request = route.calls.last.request
    assert sent_request.headers["user-agent"] == "test-agent/1.0"
    assert sent_request.url.params["limit"] == "10"


@pytest.mark.asyncio
async def test_fetch_hot_propagates_http_errors(news_hot_payload):
    with respx.mock(base_url=REDDIT_BASE) as router:
        router.get("/r/news/hot.json").mock(return_value=httpx.Response(429))
        async with RedditClient() as client:
            with pytest.raises(httpx.HTTPStatusError):
                await client.fetch_hot("news")
