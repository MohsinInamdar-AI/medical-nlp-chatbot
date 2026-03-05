from fastapi import APIRouter
from app.api.schemas import QueryRequest, QueryResponse
from app.core.config import settings
from app.core.confidence import confidence_from_scores
from app.core.errors import bad_request, not_found, server_error
from app.retrieval.sql_store import SqlStore
from app.retrieval.vector_store import VectorStore
from app.retrieval.query_router import route_sql_if_applicable
from app.llm.ollama_client import OllamaClient
from app.llm.prompting import build_prompt

router = APIRouter()

_sql: SqlStore | None = None
_vs: VectorStore | None = None
_llm: OllamaClient | None = None

def get_sql() -> SqlStore:
    global _sql
    if _sql is None:
        _sql = SqlStore(settings.sqlite_path)
    return _sql

def get_vs() -> VectorStore:
    global _vs
    if _vs is None:
        _vs = VectorStore(
            index_path=f"{settings.index_dir}/faiss.index",
            meta_path=f"{settings.index_dir}/faiss_meta.json",
        )
        _vs.load()
    return _vs

def get_llm() -> OllamaClient:
    global _llm
    if _llm is None:
        _llm = OllamaClient(settings.ollama_base_url, settings.ollama_model, settings.llm_timeout)
    return _llm

@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    mrd = (req.mrd_number or "").strip()
    q = (req.query or "").strip()

    if not mrd:
        raise bad_request("EMPTY_MRD", "Missing mrd_number", None)
    if not q:
        raise bad_request("EMPTY_QUERY", "Empty query", mrd)

    sql = get_sql()
    if not sql.mrd_exists(mrd):
        raise not_found("INVALID_MRD", f"Invalid MRD: {mrd}", mrd)

    # 1) SQL-first route for count/structured questions (no LLM)
    routed = route_sql_if_applicable(sql, mrd, q)
    if routed.handled and routed.answer:
        return QueryResponse(mrd_number=mrd, answer=routed.answer, confidence=routed.confidence or "High")
    if routed.handled and routed.code == "UNSUPPORTED_QUESTION":
        raise bad_request("UNSUPPORTED_QUESTION", routed.answer or "Unsupported question.", mrd)

    # 2) Vector retrieval (RAG)
    try:
        vs = get_vs()
        hits = vs.search(q, top_k=settings.top_k * 3)
    except Exception as e:
        raise server_error("RETRIEVAL_ERROR", f"Retrieval error: {type(e).__name__}", mrd)

    # filter to MRD
    hits = [(s, h) for (s, h) in hits if str(h.get("mrd_number")) == mrd]
    hits = hits[: settings.top_k]

    if not hits:
        return QueryResponse(
            mrd_number=mrd,
            answer="No relevant information found in the patient's records.",
            confidence="Low",
        )

    contexts = []
    scores = []
    for score, meta in hits:
        scores.append(score)
        contexts.append(meta)

    facts = sql.quick_facts(mrd)
    prompt = build_prompt(q, facts, contexts)

    llm = get_llm()
    try:
        answer = await llm.generate(prompt)
        if not answer:
            answer = "No relevant information found in the patient's records."
    except TimeoutError:
        raise server_error("LLM_TIMEOUT", "LLM timeout", mrd)
    except Exception as e:
        raise server_error("LLM_ERROR", f"LLM error: {type(e).__name__}", mrd)

    conf = confidence_from_scores(scores)
    return QueryResponse(mrd_number=mrd, answer=answer, confidence=conf)
