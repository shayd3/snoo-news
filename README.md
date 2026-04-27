# snoo-news

A small Pydantic AI agent that pulls hot posts from `r/news`, `r/worldnews`,
`r/politics`, and `r/tech`, picks the strongest stories, and prints a digest
with article links and 2-3 sentence summaries.

The agent uses Anthropic Claude Haiku 4.5 and the public unauthenticated
Reddit JSON API.

## Setup

```bash
uv sync
cp .env.example .env
# put your ANTHROPIC_API_KEY into .env
```

## Run

```bash
uv run snoo-news
```

The agent will call its `get_hot_posts` tool once per target subreddit, pick
roughly 2-3 stories per sub, and print a formatted digest to stdout.

## Test

```bash
uv run pytest
```

All tests run offline:

- `tests/test_reddit.py` mocks Reddit's JSON endpoint with `respx` and
  verifies parsing, filtering of stickied/NSFW posts, and User-Agent header.
- `tests/test_agent.py` swaps in Pydantic AI's `TestModel` so the agent loop
  runs without calling Anthropic, and asserts the `get_hot_posts` tool fires
  and a `Digest` comes back.
- `tests/test_format.py` checks the stdout formatting of a hand-built digest.

## Layout

```
src/snoo_news/
  models.py   # RedditPost, StorySummary, Digest
  reddit.py   # async RedditClient (httpx)
  agent.py    # Pydantic AI agent + get_hot_posts tool
  format.py   # Digest -> formatted log string
  main.py     # CLI entrypoint
```

## Roadmap

- Email delivery (SMTP / Resend / SES).
- Optional article-body fetch with a fallback to the post selftext.
- Scheduled run (cron / GitHub Actions).
- Dedup across runs.
