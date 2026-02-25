"""Generate embeddings using OpenRouter API with retry logic."""

import time
from typing import Optional

from openai import OpenAI

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Maximum retry attempts for transient failures
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


class EmbeddingError(Exception):
    """Raised when embedding generation fails after retries."""
    pass


def _get_client():
    settings = get_settings()
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )


def _retry_with_backoff(func, *args, **kwargs):
    """Execute a function with exponential backoff retry."""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    f"Embedding API call failed (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {delay}s",
                    error=str(e),
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"Embedding API call failed after {MAX_RETRIES} attempts",
                    error=str(e),
                )
    raise EmbeddingError(f"Failed after {MAX_RETRIES} retries: {last_error}")


def generate_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """
    Generate embedding vector for text using OpenRouter.

    Raises:
        EmbeddingError: If embedding fails after retries.
        ValueError: If text is empty.
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    settings = get_settings()
    client = _get_client()

    def _call():
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )
        embedding = response.data[0].embedding

        # Validate: reject zero vectors
        if all(v == 0.0 for v in embedding):
            raise EmbeddingError("API returned a zero vector — likely a model error")

        return embedding

    return _retry_with_backoff(_call)


def generate_embeddings_batch(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    batch_size: int = 100,
) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.

    Raises:
        EmbeddingError: If any batch fails after retries.
    """
    settings = get_settings()
    client = _get_client()

    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        # Filter empty texts — track their indices
        valid_indices = [j for j, t in enumerate(batch) if t and t.strip()]
        valid_texts = [batch[j] for j in valid_indices]

        if not valid_texts:
            # Entire batch is empty text — this is a data quality issue, not an API issue
            logger.warning(
                "Entire batch contains empty texts, skipping",
                batch_start=i,
                batch_size=len(batch),
            )
            # Return None for empty slots so caller can handle
            embeddings.extend([None] * len(batch))
            continue

        logger.debug(
            "Generating embeddings batch",
            batch_num=i // batch_size + 1,
            batch_size=len(valid_texts),
        )

        def _call():
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=valid_texts,
            )
            return response

        response = _retry_with_backoff(_call)

        # Map results back to original slots
        batch_embeddings: list[Optional[list[float]]] = [None] * len(batch)
        for idx_in_valid, embedding_data in enumerate(response.data):
            original_idx = valid_indices[idx_in_valid]
            embedding = embedding_data.embedding

            # Validate non-zero
            if all(v == 0.0 for v in embedding):
                logger.warning("Zero vector returned for text", index=i + original_idx)
                batch_embeddings[original_idx] = None
            else:
                batch_embeddings[original_idx] = embedding

        embeddings.extend(batch_embeddings)

    return embeddings


def generate_query_embedding(query: str) -> list[float]:
    """Generate embedding optimized for search queries."""
    return generate_embedding(query, task_type="RETRIEVAL_QUERY")
