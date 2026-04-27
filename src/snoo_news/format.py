from collections import defaultdict

from .models import Digest


def format_digest(digest: Digest) -> str:
    if not digest.stories:
        return "No stories found.\n"

    by_sub: dict[str, list] = defaultdict(list)
    for story in digest.stories:
        by_sub[story.subreddit].append(story)

    lines: list[str] = []
    lines.append("=" * 72)
    lines.append(f"snoo-news digest  ({len(digest.stories)} stories)")
    lines.append("=" * 72)

    for sub in sorted(by_sub):
        lines.append("")
        lines.append(f"r/{sub}")
        lines.append("-" * 72)
        for story in by_sub[sub]:
            src_tag = {
                "article": "[via article]",
                "selftext": "[via Reddit]",
                "title": "[title only]",
            }.get(story.summary_source, "")
            header = (
                f"[score={story.score}  comments={story.num_comments}]  {story.title}"
            )
            if src_tag:
                header += f"  {src_tag}"
            lines.append(header)
            lines.append(f"  {story.summary}")
            lines.append(f"  Article: {story.article_url}")
            lines.append(f"  Reddit:  {story.reddit_url}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
