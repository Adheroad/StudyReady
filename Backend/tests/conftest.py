"""Pytest fixtures and configuration."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.database.connection import Base
from app.database.models import Paper, Question


# === Settings Fixtures ===


@pytest.fixture
def test_settings():
    """Test settings with mock values."""
    return Settings(
        OPENROUTER_API_KEY="test-openrouter-key",
        DATABASE_URL="sqlite:///:memory:",
        DEBUG=True,
        ENVIRONMENT="development",
        LOG_LEVEL="DEBUG",
    )


# === Database Fixtures ===


@pytest.fixture
def db_engine():
    """In-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Database session for tests."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# === Sample Data Fixtures ===


@pytest.fixture
def sample_paper(db_session):
    """Create a sample paper in DB."""
    paper = Paper(
        subject="COMMERCIAL ART",
        grade="XII",
        year="2024",
        source_url="https://cbse.gov.in/test.pdf",
        processed=False,
    )
    db_session.add(paper)
    db_session.commit()
    return paper


@pytest.fixture
def sample_questions(db_session, sample_paper):
    """Create sample questions in DB."""
    questions = [
        Question(
            paper_id=sample_paper.id,
            question_number="1",
            question_text="Describe the characteristics of Mughal miniature painting.",
            marks=5,
            section="D",
            question_type="long",
        ),
        Question(
            paper_id=sample_paper.id,
            question_number="2",
            question_text="What is the significance of Bengal School in Indian Art?",
            marks=3,
            section="C",
            question_type="short",
        ),
        Question(
            paper_id=sample_paper.id,
            question_number="3",
            question_text="Renaissance art originated in which country?",
            marks=1,
            section="A",
            question_type="mcq",
        ),
    ]
    db_session.add_all(questions)
    db_session.commit()
    return questions


# === Mock Fixtures ===


@pytest.fixture
def mock_vision_client():
    """Mock OpenAI-compatible Vision client (used via OpenRouter)."""
    with patch("app.services.extraction.gemini_vision._get_client") as mock_get:
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content='''
        [{"question_number": "1", "question_text": "Test question", "marks": 1}]
        '''))]
        client.chat.completions.create.return_value = response
        mock_get.return_value = client
        yield mock_get


@pytest.fixture
def mock_embedding():
    """Mock embedding API (1536d for text-embedding-3-small)."""
    with patch("app.services.embeddings.gemini_embeddings._get_client") as mock_get:
        client = MagicMock()
        response = MagicMock()
        response.data = [MagicMock(embedding=[0.1] * 1536)]
        client.embeddings.create.return_value = response
        mock_get.return_value = client
        yield mock_get


@pytest.fixture
def mock_openrouter():
    """Mock OpenRouter API responses."""
    with patch("openai.OpenAI") as mock:
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content="Formatted paper"))]
        client.chat.completions.create.return_value = response
        mock.return_value = client
        yield mock


# === HTTP Fixtures ===


@pytest.fixture
def mock_requests():
    """Mock requests for CBSE scraping."""
    with patch("requests.get") as mock:
        mock.return_value.content = b"""
        <html>
        <table>
            <tr>
                <td>Commercial Art</td>
                <td><a href="papers/2024/XII/art.pdf">Download</a></td>
                <td>1.2 MB</td>
            </tr>
        </table>
        </html>
        """
        mock.return_value.raise_for_status = MagicMock()
        yield mock
