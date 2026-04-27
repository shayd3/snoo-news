from snoo_news.format import format_digest
from snoo_news.models import Digest, StorySummary


def _story(**overrides) -> StorySummary:
    base = dict(
        title="A headline",
        subreddit="news",
        summary="One. Two. Three.",
        article_url="https://example.com/article",
        reddit_url="https://www.reddit.com/r/news/comments/abc/",
        score=1234,
        num_comments=56,
    )
    base.update(overrides)
    return StorySummary(**base)


def test_format_empty_digest():
    out = format_digest(Digest(stories=[]))
    assert "No stories found" in out


def test_format_groups_by_subreddit_and_includes_fields():
    digest = Digest(
        stories=[
            _story(subreddit="news", title="News one"),
            _story(subreddit="tech", title="Tech one", score=99, num_comments=5),
            _story(subreddit="news", title="News two"),
        ]
    )
    out = format_digest(digest)

    assert "r/news" in out
    assert "r/tech" in out
    assert "News one" in out
    assert "News two" in out
    assert "Tech one" in out
    assert "score=1234" in out
    assert "score=99" in out
    assert "https://example.com/article" in out
    assert "https://www.reddit.com/r/news/comments/abc/" in out

    news_index = out.index("r/news")
    tech_index = out.index("r/tech")
    assert news_index < tech_index, "subreddits should be sorted alphabetically"


def test_format_renders_summary_source_tag():
    digest = Digest(
        stories=[
            _story(subreddit="news", title="From article", summary_source="article"),
            _story(subreddit="news", title="From selftext", summary_source="selftext"),
            _story(subreddit="news", title="From title", summary_source="title"),
        ]
    )
    out = format_digest(digest)
    assert "[via article]" in out
    assert "[via Reddit]" in out
    assert "[title only]" in out
