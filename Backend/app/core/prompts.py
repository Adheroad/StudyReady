"""Prompt management utility."""

from pathlib import Path
from functools import lru_cache

from app.core.logging import get_logger

logger = get_logger(__name__)

# Define where prompts are stored
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@lru_cache()
def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from a markdown file.

    Args:
        prompt_name: Name of the prompt file (without extension)

    Returns:
        The content of the prompt file.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    file_path = PROMPTS_DIR / f"{prompt_name}.md"

    if not file_path.exists():
        logger.error(f"Prompt file not found: {file_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_name}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            logger.debug(f"Loaded prompt: {prompt_name}")
            return content
    except Exception as e:
        logger.error(f"Failed to load prompt {prompt_name}: {e}")
        raise
