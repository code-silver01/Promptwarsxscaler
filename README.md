# LexGuard One

> **Adversarial Multi-Agent AI Contract Intelligence System**
>
> Analyzes legal documents clause-by-clause using an adversarial Red/Blue/Verdict agent pipeline to detect exploitative clauses, hidden liabilities, and legal risks before you sign.

---

## Architecture

LexGuard One uses an 8-layer processing pipeline:

| Layer | Module | Purpose |
|-------|--------|---------|
| 1 | `document_parser.py` | PDF/DOCX ingestion + clause segmentation |
| 2 | `clause_classifier.py` | Zero-shot Gemini classification + vague qualifier detection |
| 3 | `adversarial_engine.py` | Risk/Defense/Verdict three-agent debate |
| 4 | `benchmark_rag.py` | Vertex AI embeddings + Firestore benchmark comparison |
| 5 | `consequence_engine.py` | Real-world consequence chain simulation |
| 6 | `negotiation_engine.py` | Fairer clause alternative generation |
| 7 | `risk_scorer.py` | Traceable, auditable risk scoring |
| 8 | `report_generator.py` | Structured report assembly |

## Tech Stack

- **Backend:** Python 3.11, FastAPI, Pydantic v2
- **Frontend:** React 18, Tailwind CSS v4
- **AI:** Google Gemini API (Pro + Flash), Vertex AI (textembedding-gecko)
- **Storage:** Google Firestore, Google Cloud Storage
- **Deploy:** Google Cloud Run, Cloud Build CI/CD
- **Logging:** Google Cloud Logging (structured JSON)
- **Security:** Secret Manager, rate limiting, MIME validation

## Google Services Integration

| Service | Usage |
|---------|-------|
| Gemini API (`gemini-1.5-pro`) | Adversarial agents, consequences, negotiations |
| Gemini API (`gemini-1.5-flash`) | Clause classification, contradiction detection |
| Vertex AI (`textembedding-gecko`) | Clause embeddings for benchmark RAG |
| Firestore | Benchmark corpus + analysis report persistence |
| Cloud Storage | Temporary document storage |
| Cloud Run | Containerized stateless deployment |
| Cloud Build | CI/CD pipeline (`cloudbuild.yaml`) |
| Secret Manager | Secure API key storage |
| Cloud Logging | Structured JSON log output |

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8080

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Environment Variables

```bash
# Copy template and fill values
cp .env.example .env

# Required
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
FIRESTORE_DATABASE=lexguard-benchmark
GCS_BUCKET=lexguard-uploads
VERTEX_AI_LOCATION=us-central1
```

## Deploy to Cloud Run

```bash
# Build and deploy via Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Or manual deployment
docker build -t gcr.io/$PROJECT_ID/lexguard-one .
docker push gcr.io/$PROJECT_ID/lexguard-one
gcloud run deploy lexguard-one \
  --image gcr.io/$PROJECT_ID/lexguard-one \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi --cpu 2 \
  --min-instances 1 --max-instances 3
```

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

## Project Structure

```
lexguard-one/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── routers/analyze.py         # POST /api/analyze endpoint
│   ├── services/                  # 8 processing layers
│   ├── models/schemas.py          # Pydantic models for all I/O
│   ├── utils/                     # Gemini, Firestore, validators
│   ├── tests/                     # pytest test suites
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/            # React UI components
│   └── package.json
├── Dockerfile                     # Multi-stage build
├── cloudbuild.yaml                # Cloud Build CI/CD
└── .env.example                   # Environment template
```

## Risk Scoring Formula

```
Per-clause score = severity_score × category_weight × benchmark_deviation

severity_score: HIGH=3, MEDIUM=2, LOW=1
category_weight: IP_TRANSFER=1.5, NON_COMPETE=1.4, DATA_COLLECTION=1.3, ARBITRATION=1.3, others=1.0
benchmark_deviation: 0.5 + (percentile / 100) → range [0.5, 1.5]

Aggregate = (sum of clause scores / max possible) × 100

Risk Tiers: 0-25 Low, 26-50 Moderate, 51-75 High, 76-100 Critical
```

## Security

- MIME type validated from file header bytes (not extension)
- Max file size: 10MB enforced server-side
- Rate limiting: 10 req/min per IP
- No API keys in code — environment variables only
- HTML/script tags stripped from LLM inputs
- Security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection

## License

Built for PromptWars × Scaler Hackathon 2026.