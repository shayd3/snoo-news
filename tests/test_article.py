import httpx
import pytest
import respx

from snoo_news.article import BROWSER_USER_AGENT, fetch_article


ARTICLE_HTML = """<html><head><title>Headline</title></head>
<body>
<header><nav>Home About Subscribe</nav></header>
<aside class="ads">Buy now! Limited offer!</aside>
<article>
<h1>City council passes new transit plan</h1>
<p>City council voted on Tuesday to approve the new transit plan,
ending months of debate. The measure passed 7-2.</p>
<p>Funding will come from a bond measure scheduled for next spring,
according to the council president.</p>
</article>
<footer>Cookie banner. Newsletter signup.</footer>
</body></html>"""


@pytest.mark.asyncio
async def test_fetch_article_extracts_content_and_uses_browser_ua():
    with respx.mock() as router:
        route = router.get("https://example.com/story").mock(
            return_value=httpx.Response(200, html=ARTICLE_HTML)
        )
        async with httpx.AsyncClient() as client:
            result = await fetch_article("https://example.com/story", client)

    assert result is not None
    assert result.url == "https://example.com/story"
    assert "transit plan" in result.content
    assert "Buy now" not in result.content
    assert "Cookie banner" not in result.content

    sent = route.calls.last.request
    assert sent.headers["user-agent"] == BROWSER_USER_AGENT


@pytest.mark.asyncio
async def test_fetch_article_skips_known_non_article_hosts():
    with respx.mock(assert_all_called=False) as router:
        async with httpx.AsyncClient() as client:
            result = await fetch_article(
                "https://www.youtube.com/watch?v=abc", client
            )
    assert result is None
    assert not router.calls


@pytest.mark.asyncio
async def test_fetch_article_returns_none_on_http_error():
    with respx.mock() as router:
        router.get("https://example.com/blocked").mock(
            return_value=httpx.Response(403)
        )
        async with httpx.AsyncClient() as client:
            result = await fetch_article("https://example.com/blocked", client)
    assert result is None


@pytest.mark.asyncio
async def test_fetch_article_returns_none_on_empty_extraction():
    with respx.mock() as router:
        router.get("https://example.com/empty").mock(
            return_value=httpx.Response(200, html="<html><body></body></html>")
        )
        async with httpx.AsyncClient() as client:
            result = await fetch_article("https://example.com/empty", client)
    assert result is None


@pytest.mark.asyncio
async def test_fetch_article_returns_none_for_empty_url():
    async with httpx.AsyncClient() as client:
        assert await fetch_article("", client) is None
