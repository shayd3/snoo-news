from __future__ import annotations

import os

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModelSettings

from .models import ArticleContent, Digest, RedditPost
from .reddit import RedditClient

_raw_subs = os.environ.get("SNOO_SUBREDDITS", "news,tech")
TARGET_SUBREDDITS = tuple(s.strip() for s in _raw_subs.split(",") if s.strip())

SYSTEM_PROMPT = f"""\
You are a news-digest agent. Your job is to assemble a short, neutral digest of
the most newsworthy stories currently hot on Reddit.

Workflow:
1. Call the `get_hot_posts` tool once for EACH of these subreddits: {", ".join(TARGET_SUBREDDITS)}.
   Use a limit of 10. Do not skip any subreddit.
2. From the returned posts for each subreddit, choose the 2-3 strongest news stories.
   Prefer posts with high score and comment counts. Skip:
     - megathreads, weekly threads, "what are you reading" / discussion threads
     - meta posts about the subreddit itself
     - polls, memes, "I made this" personal posts
     - tabloid / clearly low-quality sources when better alternatives exist
3. For each selected post:
     - If `is_self` is False, call `get_article(post.url)` to retrieve the
       linked article body. `get_article` returns None for self-posts,
       image/video/social hosts (Reddit, imgur, YouTube, Twitter/X), paywalls,
       and fetch failures.
     - If `get_article` returns content, write a NEUTRAL 2-3 sentence summary
       grounded in that article content (ignore boilerplate/ads -- the
       extractor strips most). Set summary_source to "article".
     - Otherwise, fall back to the post title and selftext. Use
       summary_source "selftext" if selftext is non-empty, else "title".
   Do NOT invent facts the data does not support. Keep summaries neutral and
   concise (2-3 sentences).
4. Return a `Digest` containing every selected story, populating
   article_url from the post `url`, reddit_url from the post `permalink`,
   and summary_source per the rule above.

Aim for roughly 8-12 stories total across all subreddits.
"""


agent: Agent[RedditClient, Digest] = Agent(
    "anthropic:claude-haiku-4-5",
    deps_type=RedditClient,
    output_type=Digest,
    system_prompt=SYSTEM_PROMPT,
    model_settings=AnthropicModelSettings(
        # Cache the static parts (system prompt + tool schemas) for 5 minutes.
        # On a typical run the agent makes 3-4 turns; turns 2+ pay ~10% of
        # normal input-token cost for everything covered by the cache.
        anthropic_cache_instructions=True,
        anthropic_cache_tool_definitions=True,
        # Automatically cache the growing message history across turns.
        anthropic_cache=True,
    ),
)


@agent.tool
async def get_hot_posts(
    ctx: RunContext[RedditClient],
    subreddit: str,
    limit: int = 10,
) -> list[RedditPost]:
    """Fetch hot posts from a subreddit, with stickied/NSFW filtered out."""
    return await ctx.deps.fetch_hot(subreddit, limit=limit)


@agent.tool
async def get_article(
    ctx: RunContext[RedditClient],
    url: str,
) -> ArticleContent | None:
    """Fetch and extract article text. Returns None for self-posts, image/video/social hosts, paywalls, or fetch failures."""
    return await ctx.deps.fetch_article(url)


async def run_digest(client: RedditClient) -> Digest:
    result = await agent.run(
        "Build today's news digest from the four target subreddits.",
        deps=client,
    )
    return result.output
