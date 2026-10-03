# AgentDesk MVP

A multi-agent AI customer-assistant platform designed for local service businesses, built as a time-boxed MVP for the **Dafinitiq AI Engineer Associate application**.

---

## Overview

**AgentDesk MVP** demonstrates an end-to-end AI customer assistant for small businesses. Using **Apex Dental Studio** as a seeded demo business, the system handles customer inquiries through an interactive web chat, retrieves verified clinic knowledge via Retrieval-Augmented Generation (RAG), generates grounded answers without hallucinating, detects high-intent leads, scores them deterministically, and surfaces them in real time on a business-owner dashboard.

---

## Problem

Local service businesses (dental clinics, salons, law practices, auto repair shops) face two persistent challenges:
1. **Missed Opportunities**: High-intent customer inquiries arriving after hours or during peak operational hours frequently go unanswered, leading potential clients to competitors.
2. **Repetitive Staff Workload**: Receptionists spend hours answering the same routine inquiries regarding pricing, operating hours, accepted insurance, and service availability.
3. **Unstructured Inquiries**: Traditional contact forms or basic chatbots often fail to capture structured contact details and qualify buying intent effectively.

---

## Solution

AgentDesk solves this with a reliable, grounded AI customer desk:
- **Zero Hallucination Grounding**: Answers routine questions accurately using semantic vector search over verified business knowledge.
- **High-Intent Lead Capture**: Automatically extracts customer names, email addresses, and phone numbers directly from natural conversation.
- **Deterministic Scoring**: Evaluates intent and completeness to assign clear lead statuses (`HOT`, `WARM`, `COLD`) without unpredictable LLM scoring variance.
- **Real-Time Visibility**: Persists leads into PostgreSQL and presents them to clinic owners on a clean, actionable dashboard.

---

## Key Features

- **Grounded AI Customer Chat**: Real-time conversational interface powered by Groq (`openai/gpt-oss-20b`).
- **Accurate RAG Retrieval**: Local Sentence Transformers (`all-MiniLM-L6-v2`) generating 384-dimensional embeddings stored in PostgreSQL with `pgvector`.
- **Source Transparency**: Every grounded answer includes source document citations and similarity relevance scores.
- **Graceful Fallbacks**: When queries exceed available business knowledge (e.g., out-of-domain requests), the assistant declines gracefully and provides clinic contact channels rather than hallucinating services.
- **Deterministic Lead Qualification**: Rule-based scoring engine categorizing inquiries into `HOT` (100), `WARM` (70), or `COLD` (30) based on clear criteria.
- **Prompt-Injection Defense**: System instructions enforce strict role boundaries, preventing prompt extraction or instruction overrides.
- **Multi-Tenant Scoping**: Database models and vector retrieval strictly partition knowledge and leads by `business_id`.
- **Owner Dashboard**: Clean dashboard displaying recent leads, qualification status, contact details, inquiry messages, and timestamps.
- **Extensible Provider Abstraction**: Modular LLM interface supporting `GroqProvider` for production inference and `MockLLMProvider` for offline testing.

---

## Architecture

```text
Customer
   │
   ▼
Next.js Frontend (Web Chat)
   │  POST /api/v1/chat
   ▼
FastAPI Application Services
   │
   ├──▶ Lead Extractor & Scoring Service ──▶ PostgreSQL (`leads` table)
   │
   └──▶ Semantic Search Service
           │  all-MiniLM-L6-v2 (384-d vectors)
           ▼
        PostgreSQL + pgvector (Cosine Similarity)
           │
           ▼ Retrieved Knowledge Chunks
        Prompt Assembler (Strict Grounding Template)
           │
           ▼ Context + User Query
        Groq LLM Provider (`openai/gpt-oss-20b`)
           │
           ▼ Grounded Answer + Source Citations
Customer Web Chat Response
   │
   ▼
Owner Dashboard (`/dashboard`) ◀── PostgreSQL
```

---

## AI and RAG Pipeline

1. **Document Ingestion & Chunking**:
   - Seed documents (Business Overview, Operating Hours, Services & Pricing, FAQs) are split into semantic chunks with metadata tracking document titles, source types, and business ownership.
2. **Vector Embeddings**:
   - Chunks are embedded using HuggingFace's `sentence-transformers/all-MiniLM-L6-v2` locally on the server.
   - Embeddings are 384-dimensional dense vectors stored using PostgreSQL `pgvector`.
3. **Semantic Similarity Search**:
   - Incoming customer questions are embedded and queried against the business's vector index using cosine distance (`<=>`).
   - Tenant isolation is strictly enforced via `WHERE business_id = :business_id`.
4. **Relevance Thresholding**:
   - Retrieved chunks must exceed a minimum relevance threshold (`MIN_RELEVANCE_THRESHOLD = 0.22`) to prevent noise from entering the context.
   - If no relevant knowledge is found, a deterministic fallback message with clinic contact info is returned immediately without querying the LLM.
5. **Grounded Generation**:
   - Chunks above threshold are assembled into a structured context block.
   - The system prompt instructs the model to rely solely on the provided context, adhere strictly to clinic facts, and refuse out-of-scope inquiries.

---

## Lead Detection and Scoring

The platform extracts and scores leads deterministically without relying on unpredictable LLM scoring:

### 1. Information Extraction
- **Regex & Token Extraction**: Extracts name patterns, email addresses (`RFC 5322` regex), and phone numbers (`E.164` / formatted standard numbers) safely from conversation messages.

### 2. Intent Classification
- Detects buying and appointment signals (e.g., `"book"`, `"appointment"`, `"schedule"`, `"consultation"`).
- Distinguishes high-intent booking inquiries from informational pricing questions and routine FAQ browsing.

### 3. Scoring Rules
| Status | Score | Criteria |
| :--- | :---: | :--- |
| **HOT** | `100` | Explicit booking/appointment intent **and** valid contact info (email or phone). |
| **WARM** | `70` | Pricing or service inquiry with contact info, OR explicit booking intent without contact info. |
| **COLD** | `30` | Routine question with contact details provided, but without immediate booking intent. |

Captured leads are committed to the PostgreSQL `leads` table and instantly made visible in the owner dashboard.

---

## Security and Safety

- **Server-Side API Keys**: AI provider keys (`GROQ_API_KEY`) reside exclusively in backend environment variables and are never transmitted to the frontend.
- **SQL Injection Prevention**: All database interactions use SQLAlchemy 2.0 ORM parameterization and asyncpg; LLMs are never permitted to generate or execute raw SQL.
- **Prompt-Injection Neutralization**: System prompts place instructions in high-priority system contexts with explicit guardrails against jailbreaks, persona hijacking, and instruction overrides.
- **Tenant Isolation**: All vector queries, knowledge chunk retrievals, and lead access operations require and filter by `business_id`.
- **Environment Isolation**: `.env` is gitignored; `.env.example` provides safe developer defaults without credentials.

---

## Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 16 (App Router), React, TypeScript | Customer chat UI and business-owner dashboard |
| **Styling** | Tailwind CSS, Lucide Icons | Responsive, modern UI |
| **Backend** | Python 3.13, FastAPI, Pydantic v2 | High-performance asynchronous REST API |
| **Database** | PostgreSQL 16 with `pgvector` 0.8.7 | Relational data and vector similarity storage |
| **ORM & Migrations** | SQLAlchemy 2.0 (AsyncIO), Alembic | Schema definition and automated migrations |
| **Cache / Queue** | Redis 7 | Infrastructure foundation for background tasks |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Local 384-dimensional dense semantic vectors |
| **LLM Inference** | Groq Cloud SDK (`openai/gpt-oss-20b`) | Ultra-fast grounded language model inference |
| **Testing** | Pytest, pytest-asyncio, HTTPX | Automated test suite (25/25 passing) |
| **Containerization**| Docker & Docker Compose | Containerized PostgreSQL + pgvector and Redis |

---

## Project Structure

```text
AgentDesk-MVP/
├── docker-compose.yml           # PostgreSQL (pgvector) and Redis services
├── .env.example                 # Environment configuration template
├── README.md                    # Project documentation
│
├── backend/                     # FastAPI Backend Application
│   ├── alembic/                 # Database migrations (PostgreSQL + pgvector)
│   ├── app/
│   │   ├── api/v1/              # Versioned API routes (/chat, /leads, /business, /health)
│   │   ├── core/                # App configuration, database connection, logging
│   │   ├── models/              # SQLAlchemy models (Business, Knowledge, Lead)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── seeds/               # Seed service and Apex Dental Studio dataset
│   │   └── services/
│   │       ├── chat.py          # Chat orchestration service
│   │       ├── prompt.py        # System prompt builder & safety constraints
│   │       ├── embedding/       # Embedding provider abstraction (all-MiniLM-L6-v2)
│   │       ├── lead/            # Lead extraction and deterministic scoring
│   │       ├── llm/             # LLM provider abstraction (GroqProvider, MockLLMProvider)
│   │       └── rag/             # Document ingestion, chunking, and semantic search
│   ├── scripts/                 # Verification and utility scripts
│   ├── tests/                   # Pytest automated test suite (25 tests)
│   └── requirements.txt         # Python dependencies
│
└── frontend/                    # Next.js Frontend Application
    ├── src/
    │   └── app/
    │       ├── layout.tsx       # Root layout
    │       ├── page.tsx         # Customer web chat interface
    │       └── dashboard/       # Business owner lead dashboard
    ├── package.json             # Frontend dependencies
    └── tsconfig.json            # TypeScript configuration
```

---

## Prerequisites

Before running the application, ensure you have:
- **Docker & Docker Compose** (for PostgreSQL with pgvector and Redis)
- **Python 3.11+** (Python 3.13 recommended)
- **Node.js 18+** (Node.js 20+ recommended) and `npm`
- **Groq API Key** (obtainable for free at [groq.com](https://groq.com))

---

## Environment Variables

Copy the template to create your local `.env`:

```bash
cp .env.example .env
```

Key variables configured in `.env`:

```ini
# Application
PROJECT_NAME="AgentDesk MVP"
ENVIRONMENT="development"
DEBUG=true

# Database (PostgreSQL + pgvector)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5434/agentdesk
SYNC_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5434/agentdesk

# Redis
REDIS_URL=redis://localhost:6379/0

# Groq LLM
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

# Embeddings (Local Sentence Transformers)
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Local Setup

### 1. Start Database & Infrastructure

Start PostgreSQL (with `pgvector`) and Redis in the background:

```bash
docker compose up -d
```

Verify containers are running:
```bash
docker ps
```
*(PostgreSQL should be accessible on port `5434`, Redis on port `6379`)*.

---

## Running the Backend

### 1. Set Up Python Virtual Environment

```bash
cd backend
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations

Apply Alembic migrations to create tables and initialize the `vector` extension:

```bash
alembic upgrade head
```

### 4. Start FastAPI Server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Base URL: `http://127.0.0.1:8000`
- Swagger Documentation: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/v1/health`

*(On first startup, the application automatically seeds Apex Dental Studio along with its knowledge documents and vector embeddings).*

---

## Running the Frontend

### 1. Install Node Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

- Customer Chat Interface: `http://localhost:3000`
- Business Owner Dashboard: `http://localhost:3000/dashboard`

---

## Running Tests

### Backend Test Suite

Run all automated unit, integration, RAG, and isolation tests:

```bash
cd backend
pytest -q
```

All 25 tests execute against the test database and vector search pipeline.

### Frontend Production Build

Validate TypeScript types, Turbopack bundling, and static page generation:

```bash
cd frontend
npm run build
```

---

## Demo Flow

To demonstrate the full end-to-end functionality:

1. **Verify Services & Grounded Pricing**:
   - **User sends**: *"How much does teeth whitening cost and what does it include?"*
   - **Assistant responds**: States the exact $350 in-office Zoom laser whitening price, mentions the 60-minute session and custom take-home trays with gel ($200), citing the `Dental Services & Pricing Guide` source document.
2. **Verify Operating Hours**:
   - **User sends**: *"What are your opening hours?"*
   - **Assistant responds**: Monday–Friday 8:00 AM – 6:00 PM, Saturday 9:00 AM – 2:00 PM, closed on Sundays. No lead is created.
3. **Verify Lead Detection & Deterministic Scoring**:
   - **User sends**: *"I want to book teeth whitening. My name is Ali and my email is ali@example.com."*
   - **Assistant responds**: Provides direct booking contact options.
   - **Backend action**: Extracts `name="Ali"`, `email="ali@example.com"`, identifies `booking` intent, assigns deterministic score `100` (`HOT`), and commits the lead to PostgreSQL.
4. **Verify Out-of-Domain Safety (Zero Hallucination)**:
   - **User sends**: *"Do you perform brain surgery?"*
   - **Assistant responds**: Politely informs the user that this service is not available in clinic records and provides the office phone number. No hallucinated service is invented.
5. **View Owner Dashboard**:
   - Navigate to `http://localhost:3000/dashboard`.
   - View Ali's newly captured lead with status `HOT`, score `100`, email, message preview, and submission timestamp.

---

## Verification Results

The MVP has undergone full end-to-end automated and manual verification:

- **Backend Test Suite**: **25/25 tests passing** across database models, tenant isolation, pgvector cosine search, lead extraction, and API endpoints.
- **Live Groq LLM Integration**: Confirmed active and communicating with Groq's API endpoint (`POST https://api.groq.com/openai/v1/chat/completions`) using model `openai/gpt-oss-20b`.
- **RAG Grounding**: Grounded answers validated against Apex Dental Studio documents with source citations and relevance scores returned.
- **Prompt-Injection Defense**: Validated against jailbreaks; system instructions and secret credentials remain confidential.
- **Deterministic Lead Qualification**: Verified lead detection, contact extraction, and score persistence (`HOT` = 100) in PostgreSQL.
- **Multi-Tenant Isolation**: Tested cross-tenant queries to guarantee zero data leakage between distinct business IDs.
- **Frontend Production Build**: `npm run build` succeeds (5/5 static pages prerendered, 0 TypeScript or build errors).

---

## Current Scope

This time-boxed MVP focuses strictly on core customer engagement and lead capture:
- Pre-seeded single business: **Apex Dental Studio**.
- Real-time customer chat with RAG knowledge retrieval.
- Local vector embeddings via Sentence Transformers.
- Real Groq LLM inference with provider fallback.
- Deterministic lead detection, extraction, scoring, and persistence.
- Business owner lead dashboard.

---

## Future Improvements

1. **Self-Service Knowledge Management**: In-browser document upload (PDF, DOCX) and automated web crawling for business onboarding.
2. **Appointment Scheduling**: Direct two-way calendar sync (Google Calendar, Cal.com API) for automated booking slots.
3. **Omnichannel Channels**: WhatsApp Business API, SMS, and email notifications for clinic staff when a HOT lead is captured.
4. **Voice Agent Support**: WebRTC and telephony voice agent integration for incoming phone reception.
5. **Human-in-the-Loop Handover**: Real-time receptionist notification and live takeover when a customer requests human assistance.

---

## Disclaimer / MVP Scope

This repository contains the time-boxed MVP of **AgentDesk**, developed specifically for the **Dafinitiq AI Engineer Associate application**. It is designed to prove the core product architecture, practical AI engineering, and grounded retrieval pipeline. It is separate from the comprehensive university FYP implementation (`AgentDesk-FYP`).