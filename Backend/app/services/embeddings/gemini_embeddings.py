"""Generate embeddings using OpenRouter API."""


from openai import OpenAI

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_client():
    settings = get_settings()
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )


def generate_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """
    Generate embedding vector for text using OpenRouter.
    Note: task_type is ignored for OpenAI-compatible embedding endpoints typically,
    but kept for interface compatibility.
    """
    settings = get_settings()
    client = _get_client()

    if not text or not text.strip():
        logger.warning("Empty text provided for embedding")
        return [0.0] * 1536  # Default dimension for text-embedding-3-small is usually 1536

    try:
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}", extra={"exception": e})
        raise


def generate_embeddings_batch(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    batch_size: int = 100,
) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.
    """
    settings = get_settings()
    client = _get_client()
    
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        # Filter empty texts
        valid_indices = [j for j, t in enumerate(batch) if t and t.strip()]
        valid_texts = [batch[j] for j in valid_indices]

        if not valid_texts:
            embeddings.extend([[0.0] * 1536] * len(batch))
            continue

        logger.debug(
            "Generating embeddings batch",
            batch_num=i // batch_size + 1,
            batch_size=len(valid_texts),
        )

        try:
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=valid_texts,
            )
            
            # Map results back to original slots (handling empties)
            batch_embeddings = [[0.0] * 1536] * len(batch)
            for idx_in_valid, embedding_data in enumerate(response.data):
                 original_idx = valid_indices[idx_in_valid]
                 batch_embeddings[original_idx] = embedding_data.embedding
            
            embeddings.extend(batch_embeddings)

        except Exception as e:
            logger.error(f"Failed to embed batch: {e}", extra={"exception": e})
            # Fallback
            embeddings.extend([[0.0] * 1536] * len(batch))

    return embeddings


def generate_query_embedding(query: str) -> list[float]:
    """Generate embedding optimized for search queries."""
    # OpenRouter/OpenAI models generally don't distinct task types like Gemini
    return generate_embedding(query, task_type="RETRIEVAL_QUERY")
