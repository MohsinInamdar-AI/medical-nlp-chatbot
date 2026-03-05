# Medical NLP Chatbot – Technical Assessment (Hybrid Retrieval + Local LLM)

Implements the assessment requirements:
- `POST /query`
- **Hybrid Retrieval Architecture**:
  - SQL (SQLite) for structured retrieval and count questions
  - Vector semantic retrieval (FAISS) for RAG
- **Local LLM only** (Ollama) — no external APIs

## Architecture Diagram

```
                 +-------------------+
Client           |   POST /query     |
(mrd, question)->|  FastAPI (app)    |
                 +---------+---------+
                           |
           +---------------+----------------+
           |                                |
           v                                v
+---------------------+          +------------------------+
| SQLite (structured) |          | FAISS Vector Index     |
| - validate MRD      |          | - semantic retrieval   |
| - counts (visits)   |          | - top-k chunks         |
| - doc metadata      |          +-----------+------------+
+----------+----------+                      |
           |                                  v
           |                        +---------------------+
           |                        | Prompt Builder      |
           |                        | - clinical tone     |
           |                        | - no speculation    |
           |                        +----------+----------+
           |                                   |
           v                                   v
     (facts if any)                   +---------------------+
                                     | Local LLM (Ollama)   |
                                     | /api/generate        |
                                     +----------+----------+
                                                |
                                                v
                                     +---------------------+
                                     | JSON Answer +       |
                                     | confidence          |
                                     +---------------------+
```

## Model Choice
Default: `phi3` via Ollama (editable in `.env`).  
You can switch to any locally available Ollama model.

## Retrieval Strategy
1. Validate MRD using SQLite
2. Route count/structured queries to SQLite (no LLM)
3. Otherwise:
   - vector search over chunked patient text (FAISS)
   - filter results to the requested MRD
   - pass excerpts + structured facts to local LLM (RAG)

## Chunking Logic
- HTML -> plain text via BeautifulSoup
- Character chunks (~900 chars) with overlap (~120)
- Each chunk stores metadata: MRD, doc_id, doc type, form name, dates

## Prompt Design
Enforced rules:
- Clinical tone only
- No assumptions / no speculation
- No added knowledge beyond excerpts
- If answer not present: **"No relevant information found in the patient's records."**

## Error Handling
Structured JSON errors with HTTP status codes:
- 400: empty MRD / empty query / unsupported question
- 404: invalid MRD
- 500: retrieval error / LLM timeout / LLM error

## Run Locally

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 2) Start Ollama
```bash
ollama serve
ollama pull llama3.1:8b
```

### 3) Build indexes
```bash
python -m scripts.build_index
```

### 4) Start API
```bash
uvicorn app.main:app --reload
```

## Demo (curl)

Health:
```bash
curl http://127.0.0.1:8000/health
```

Query:
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"mrd_number":"17319","query":"What medications was the patient discharged with?"}'
```

Count question (SQL-only):
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"mrd_number":"17319","query":"How many visits are recorded for this patient?"}'
```
