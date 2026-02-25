"""Unit tests for extraction service."""

import pytest
from unittest.mock import MagicMock, patch


class TestGeminiVisionExtraction:
    """Unit tests for Gemini Vision extraction."""

    @pytest.mark.unit
    def test_parse_json_response_clean(self):
        """Should parse clean JSON response."""
        from app.services.extraction.gemini_vision import _parse_json_response

        text = '[{"question_number": "1", "question_text": "Test", "marks": 5}]'
        result = _parse_json_response(text)

        assert len(result) == 1
        assert result[0]["question_text"] == "Test"

    @pytest.mark.unit
    def test_parse_json_response_with_markdown(self):
        """Should strip markdown code blocks."""
        from app.services.extraction.gemini_vision import _parse_json_response

        text = """
        ```json
        [{"question_number": "1", "question_text": "Test", "marks": 5}]
        ```
        """
        result = _parse_json_response(text)

        assert len(result) == 1

    @pytest.mark.unit
    def test_parse_json_response_invalid(self):
        """Should return empty list for invalid JSON."""
        from app.services.extraction.gemini_vision import _parse_json_response

        text = "not valid json"
        result = _parse_json_response(text)

        assert result == []

    @pytest.mark.unit
    def test_validate_extracted_questions_filters_empty(self):
        """Should filter out questions without text."""
        from app.services.extraction.gemini_vision import validate_extracted_questions

        questions = [
            {"question_text": "Valid question", "marks": 1},
            {"question_text": "", "marks": 1},
            {"marks": 1},  # No question_text
        ]
        result = validate_extracted_questions(questions)

        assert len(result) == 1
        assert result[0]["question_text"] == "Valid question"

    @pytest.mark.unit
    def test_validate_extracted_questions_sets_defaults(self):
        """Should set default values for missing fields."""
        from app.services.extraction.gemini_vision import validate_extracted_questions

        questions = [{"question_text": "Test question"}]
        result = validate_extracted_questions(questions)

        assert result[0]["marks"] == 1
        assert result[0]["question_type"] == "short"
        assert result[0]["section"] == ""


class TestEmbeddings:
    """Unit tests for embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self):
        """Should return zeros for empty text."""
        from app.services.embeddings.gemini_embeddings import generate_embedding
        
        # Reset any mock state
        with patch("app.services.embeddings.gemini_embeddings._get_client") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client
            
            result = generate_embedding("")
            
            assert len(result) == 1536
            assert all(v == 0.0 for v in result)

    @pytest.mark.asyncio
    async def test_generate_embedding_valid_text(self):
        """Should return embedding for valid text."""
        from app.services.embeddings.gemini_embeddings import generate_embedding
        
        with patch("app.services.embeddings.gemini_embeddings._get_client") as mock_get:
            mock_client = MagicMock()
            mock_resp = MagicMock()
            mock_resp.data = [MagicMock(embedding=[0.1]*1536)]
            mock_client.embeddings.create.return_value = mock_resp
            mock_get.return_value = mock_client
            
            result = generate_embedding("Test text")
            
            assert len(result) == 1536
            assert result[0] == 0.1
