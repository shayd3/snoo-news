from typing import Literal

from pydantic import BaseModel, Field


class RedditPost(BaseModel):
    subreddit: str
    title: str
    url: str
    permalink: str
    score: int
    num_comments: int
    selftext: str = ""
    is_self: bool = False
    over_18: bool = False
    stickied: bool = False


class ArticleContent(BaseModel):
    url: str
    title: str | None = None
    content: str


class StorySummary(BaseModel):
    title: str
    subreddit: str
    summary: str = Field(description="2-3 sentence neutral summary of the story.")
    article_url: str
    reddit_url: str
    score: int
    num_comments: int
    summary_source: Literal["article", "selftext", "title"] = "title"


class Digest(BaseModel):
    stories: list[StorySummary]
