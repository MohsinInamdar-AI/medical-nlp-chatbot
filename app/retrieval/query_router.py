import re
from dataclasses import dataclass
from app.retrieval.sql_store import SqlStore

_count_patterns = [
    re.compile(r"\bhow many\b", re.I),
    re.compile(r"\bcount\b", re.I),
    re.compile(r"\bnumber of\b", re.I),
]

_doc_type_patterns = [
    re.compile(r"\bdocuments?\b", re.I),
    re.compile(r"\brecords?\b", re.I),
    re.compile(r"\bnotes?\b", re.I),
]

_visit_patterns = [
    re.compile(r"\bvisits?\b", re.I),
    re.compile(r"\bopd\b", re.I),
    re.compile(r"\bipd\b", re.I),
    re.compile(r"\badmissions?\b", re.I),
]

_unsafe_general_med = re.compile(r"\b(should i|what should|treat me|diagnose me|is this serious|what do i do)\b", re.I)

@dataclass
class RoutedAnswer:
    handled: bool
    answer: str | None = None
    confidence: str | None = None
    code: str | None = None  # for unsupported

def route_sql_if_applicable(sql: SqlStore, mrd: str, query: str) -> RoutedAnswer:
    """Answer strictly structured/count questions via SQL (no LLM needed)."""
    if _unsafe_general_med.search(query):
        return RoutedAnswer(handled=True, code="UNSUPPORTED_QUESTION",
                            answer="Unsupported question. This system answers only from the patient's records and cannot provide general medical advice.",
                            confidence="Low")

    if any(p.search(query) for p in _count_patterns):
        # visits?
        if any(p.search(query) for p in _visit_patterns):
            n = sql.count_visits(mrd)
            return RoutedAnswer(handled=True, answer=f"Total recorded visits for MRD {mrd}: {n}.", confidence="High")
        # documents?
        if any(p.search(query) for p in _doc_type_patterns):
            n = sql.count_documents(mrd)
            return RoutedAnswer(handled=True, answer=f"Total clinical documents available for MRD {mrd}: {n}.", confidence="High")
        # by document type
        if "type" in query.lower() or "document type" in query.lower():
            rows = sql.count_by_document_type(mrd)
            parts = [f"{dt}: {c}" for dt, c in rows[:10]]
            txt = "; ".join(parts) if parts else "No documents found."
            return RoutedAnswer(handled=True, answer=f"Document counts by type for MRD {mrd}: {txt}.", confidence="High")

    return RoutedAnswer(handled=False)
