# StudyReady 🎓
### AI-Powered CBSE Question Paper Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Vue: 3.5+](https://img.shields.io/badge/Vue-3.5+-green.svg)](https://vuejs.org/)
[![Status: In Development](https://img.shields.io/badge/Status-In_Development-orange.svg)](#)

StudyReady is a production-grade automated system designed to generate CBSE-compliant question papers using advanced Retrieval-Augmented Generation (RAG). It automates the entire pipeline: from scraping official CBSE resources and extracting questions using Gemini Vision, to generating pixel-perfect, bilingual PDFs with strict schema validation.

---

## 📖 Table of Contents
- [StudyReady 🎓](#studyready-)
    - [AI-Powered CBSE Question Paper Generator](#ai-powered-cbse-question-paper-generator)
  - [📖 Table of Contents](#-table-of-contents)
  - [🎯 Overview](#-overview)
  - [🏗️ Architecture](#️-architecture)
    - [Design Decisions](#design-decisions)
  - [✨ Key Features](#-key-features)
  - [🛠️ Tech Stack](#️-tech-stack)
    - [Model Details](#model-details)
  - [🚀 Installation Guide](#-installation-guide)
    - [Prerequisites](#prerequisites)
    - [Step-by-Step Setup](#step-by-step-setup)
  - [💡 Usage Instructions](#-usage-instructions)
    - [1. Ingesting Source Material (Admin)](#1-ingesting-source-material-admin)
    - [2. Generating a Question Paper](#2-generating-a-question-paper)
    - [3. Downloading the PDF](#3-downloading-the-pdf)
  - [📂 Project Structure](#-project-structure)
  - [⚙️ Configuration](#️-configuration)
  - [🔌 API Documentation](#-api-documentation)
    - [Papers Endpoint](#papers-endpoint)
    - [Admin Endpoint](#admin-endpoint)
  - [🧪 Testing](#-testing)
    - [Backend (Python/Pytest)](#backend-pythonpytest)
    - [Frontend (Vite)](#frontend-vite)
  - [⚠️ Known Limitations](#️-known-limitations)
  - [🗺️ Roadmap](#️-roadmap)
  - [🤝 Contribution Guidelines](#-contribution-guidelines)
  - [📜 License](#-license)
  - [✉️ Contact](#️-contact)
---

## 🎯 Overview

Generating high-quality, CBSE-compliant question papers is a manual, error-prone task for educators. StudyReady solves this by:
1.  **Automating Content Ingestion**: Scrapes official CBSE websites to build a verified vector database of past questions.
2.  **Intelligent Selection**: Uses RAG to select contextually relevant questions that match specific blueprints.
3.  **Bilingual Generation**: Automatically generates questions in both English and Hindi (Devanagari) in a split layout.
4.  **Formatting Compliance**: Produces PDFs that match the exact typography, layout, and section breakdown of official 2025 CBSE papers.

---

## 🏗️ Architecture

StudyReady follows a modern **Client-Server** architecture with specialized background workers for heavy lifting.

```mermaid
graph TD
    User((User)) -->|Browser| Frontend[Frontend: Vue 3]
    Frontend -->|REST API| Backend[Backend: FastAPI]
    
    subgraph Data Processing Pipeline
        Backend -->|Queue Task| Ingestor[CBSE Scraper & Downloader]
        Ingestor -->|PDF| Vision[Gemini Vision Engine]
        Vision -->|Extracted JSON| Embedder[Gemini Embedding-004]
        Embedder -->|Vectors| DB[(PostgreSQL + pgvector)]
    end

    subgraph Generation Pipeline
        Backend -->|RAG Query| Retrievier[Semantic search]
        Retrievier -->|Context| LLM[OpenRouter: GPT-4o/Grok]
        LLM -->|Structured JSON| Templater[Jinja2 + WeasyPrint]
        Templater -->|PDF| User
    end
```

### Design Decisions
-   **FastAPI**: Chosen for its high performance and native support for asynchronous background tasks (essential for PDF extraction).
-   **pgvector**: Integrated directly into PostgreSQL to avoid the overhead of a separate vector database while maintaining relational integrity for user/paper data.
-   **Gemini Vision**: Utilized for its superior OCR capabilities in preserving bilingual (Eng/Hin) structure from complex PDF layouts.

---

## ✨ Key Features

-   **📄 CBSE-Compliant Output**: Pixel-perfect recreation of official CBSE 2025 formats.
-   **🌐 Bilingual Support**: Seamless English + Hindi (Devanagari) split layout.
-   **🤖 RAG-Powered Intelligent Search**: Vector search ensures questions are contextually relevant and varied.
-   **⚡ Async Background Processing**: Heavy OCR and embedding tasks run as background threads to ensure UI responsiveness.
-   **🎨 Dynamic Templating**: Uses WeasyPrint with custom CSS to achieve professional typography (Times New Roman) and layout markers.
-   **📊 Strict Schema Validation**: Pydantic models ensure LLM output always adheres to the required paper structure.

---

## 🛠️ Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | Vue 3 + Vite | High performance, reactive state management (Pinia), and GSAP for micro-animations. |
| **Backend** | FastAPI | Async-first, high throughput, and automatic OpenAPI documentation. |
| **Database** | PostgreSQL + pgvector | Industry standard for relational data with robust vector search capabilities. |
| **LLM Gateway** | OpenRouter | Unified access to GPT-4o, Claude 3.5, and Gemini, enabling easy model swapping without code changes. |
| **OCR/Vision** | Gemini 1.5 Pro | State-of-the-art multimodal extraction for complex, multi-column bilingual PDFs. |
| **PDF Rendering** | WeasyPrint | High-fidelity HTML-to-PDF conversion with support for complex CSS (paged media). |
### Model Details

- **Generation Model**: `google/gemini-2.0-flash-001` (via OpenRouter) – used for paper generation and formatting. Highly recommended over Lite for blueprint compliance.
- **Vision Model**: `google/gemini-2.0-flash-001` – employed for OCR and question extraction from CBSE PDFs.
- **Embedding Model**: `openai/text-embedding-3-small` – creates vector embeddings for semantic search.
- **Database**: PostgreSQL **16** with `pgvector` extension for efficient similarity search.

---

## 🚀 Installation Guide

### Prerequisites
-   [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) (ensure your user has permission to access the Docker daemon; you may need to run commands with `sudo` or add your user to the `docker` group)
-   API Keys for OpenRouter and Gemini

### Step-by-Step Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/adhero/StudyReady.git
    cd StudyReady
    ```

2.  **Configure Environment Variables**
    Copy the example environment file and fill in your keys:
    ```bash
    cp Backend/.env.example Backend/.env
    # Edit Backend/.env with your API keys:
    # OPENROUTER_API_KEY=sk-or-...
    # GEMINI_API_KEY=AIzaSy...
    ```

3.  **Start Services via Docker**
    ```bash
    sudo docker compose up -d --build
    ```
    (Using `sudo` ensures Docker has the necessary permissions.)

4.  **Verify Services**
    -   Frontend: [http://localhost:80](http://localhost:80)
    -   Backend Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 💡 Usage Instructions

### 1. Ingesting Source Material (Admin)
Before generating papers, you must populate the vector database with official questions.
```bash
curl -X POST "http://localhost:8000/api/v1/admin/extract?subject=commercial%20art&grade=XII&limit=5"
```

### 2. Generating a Question Paper
Trigger the RAG-based generation pipeline:
```bash
curl -X POST "http://localhost:8000/api/v1/papers/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Commercial Art",
    "grade": "XII",
    "year": "2025",
    "total_marks": 36,
    "language": "both"
  }'
```

### 3. Downloading the PDF
Use the `paper_id` from the previous step to download:
```bash
curl "http://localhost:8000/api/v1/papers/{paper_id}/download?format=pdf" -o paper.pdf
```

---

## 📂 Project Structure

```text
StudyReady/
├── Backend/
│   ├── app/                # FastAPI application core
│   │   ├── api/            # Route controllers & Pydantic schemas
│   │   ├── services/       # Business logic (RAG, Extraction, PDF)
│   │   └── templates/      # Jinja2 HTML templates for PDF rendering
│   ├── alembic/            # Database migrations
│   └── scripts/            # Utility scripts for data refinement
├── Frontend/
│   ├── src/
│   │   ├── components/     # UI design system
│   │   ├── stores/         # Application state (Pinia)
│   │   └── pages/          # View components
│   └── nginx.conf          # Production frontend config
├── docker-compose.yaml      # Multi-service orchestration
└── README.md               # You are here
```

---

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GENERATION_MODEL` | LLM used for paper synthesis (OpenRouter) | `google/gemini-2.0-flash-001` |
| `VISION_MODEL` | LLM used for OCR/OCR extraction | `google/gemini-2.0-flash-001` |
| `EMBEDDING_MODEL` | Model for generating vector embeddings | `openai/text-embedding-3-small` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://studyready:password@localhost:5432/studyready` |
| `DB_PASSWORD` | Database password | `password` |

**Changing the Database Password**  
To update the DB password, edit `Backend/.env` and modify both `DB_PASSWORD` and the password part of `DATABASE_URL`:

```bash
DB_PASSWORD=new_secure_password
DATABASE_URL=postgresql://studyready:new_secure_password@localhost:5432/studyready
```

After saving, restart the containers:

```bash
sudo docker compose down
sudo docker compose up -d --build
```

---

## 🔌 API Documentation

### Papers Endpoint
-   `POST /api/v1/papers/generate`: Generates a new paper.
-   `GET /api/v1/papers/{id}`: Retrieves metadata for a specific paper.
-   `GET /api/v1/papers/{id}/download`: Streams the generated PDF/DOCX.

### Admin Endpoint
-   `POST /api/v1/admin/extract`: Triggers the scraping and ingestion worker.
-   `GET /api/v1/admin/status`: Returns current ingestion statistics.

---

## 🧪 Testing

### Backend (Python/Pytest)
```bash
cd Backend
pytest tests/unit
pytest tests/integration
```

### Frontend (Vite)
```bash
cd Frontend
npm run dev # Interactive dev server
```

---

## ⚠️ Known Limitations
-   **Subject Focus**: Currently optimized for "Commercial Art" (XII). Other subjects may require template adjustments.
-   **OCR Hallucinations**: Complex diagrams or handwritten notes in source PDFs may occasionally lead to extraction errors.
-   **Rate Limits**: Dependent on OpenRouter/Gemini API tier limits.

---

## 🗺️ Roadmap
- [ ] **Multi-Subject Blueprints**: Template support for Science, Commerce, and Humanities.
- [ ] **Interactive Editor**: Frontend UI to manually swap or edit generated questions before PDF export.
- [ ] **Adaptive Difficulty**: AI-driven difficulty scaling based on bloom's taxonomy.
- [ ] **Offline OCR**: Integration with local Tesseract/PaddleOCR for cost reduction.

---

## 🤝 Contribution Guidelines
We welcome contributions! 
1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes following [Conventional Commits](https://www.conventionalcommits.org/).
4.  Push to the branch and open a Pull Request.

---

## 📜 License
Distibuted under the MIT License. See [LICENSE](LICENSE) for more information.

---

## ✉️ Contact
**Author**: adhero
**Project Link**: [https://github.com/adhero/StudyReady](https://github.com/adhero/StudyReady)
