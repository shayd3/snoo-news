import json
import os
from pathlib import Path

import pytest

# Pydantic AI's Anthropic provider validates the API key at agent construction
# time. Tests use TestModel and never call Anthropic, but the construction
# still happens at import — give it a placeholder.
if not os.environ.get("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = "test-key-not-used"

# Pin subreddits so tests are independent of the local .env.
os.environ["SNOO_SUBREDDITS"] = "news,tech"

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def news_hot_payload() -> dict:
    return json.loads((FIXTURE_DIR / "news_hot.json").read_text())
