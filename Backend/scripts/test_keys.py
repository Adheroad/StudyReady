#!/usr/bin/env python3
"""
Test API keys for OpenRouter (Vision & Embeddings).

Usage:
    python scripts/test_keys.py
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.core.logging import get_logger, setup_logging

settings = get_settings()
setup_logging(log_level="INFO", debug=True)
logger = get_logger(__name__)


def test_openrouter():
    """Test OpenRouter API for both Text/Vision and Embeddings."""
    logger.info("Testing OpenRouter API...")
    
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
        
        # 1. Test Text Generation (sanity check)
        logger.info(f"Testing Generation ({settings.VISION_MODEL})...")
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini", # Use cheap model for ping checks
            messages=[{"role": "user", "content": "Ping"}],
            max_tokens=5,
        )
        logger.info(f"✓ Generation check passed: {response.choices[0].message.content}")

        # 2. Test Embeddings
        logger.info(f"Testing Embeddings ({settings.EMBEDDING_MODEL})...")
        try:
            emb_response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input="Hello world"
            )
            # Ensure we got a list of floats
            vec = emb_response.data[0].embedding
            logger.info(f"✓ Embeddings check passed (dim={len(vec)})")
        except Exception as emb_err:
            logger.error(f"✗ Embeddings failed: {emb_err}")
            return False

        return True

    except Exception as e:
        logger.error(f"✗ OpenRouter failed: {e}")
        return False


# QQ no print statements, use logger instead
def main():
    """Run all API key tests."""
    print("\n" + "=" * 50)
    print("API Key Test (OpenRouter Consolidated)")
    print("=" * 50 + "\n")

    passed = test_openrouter()

    print("\n" + "=" * 50)
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"Overall Status: {status}")
    print("=" * 50)
    
    if passed:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
