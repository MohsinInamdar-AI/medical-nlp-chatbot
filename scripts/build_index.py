import json
import os
from pathlib import Path

from app.retrieval.text_utils import html_to_text, chunk_text
from app.retrieval.sql_store import SqlStore, PatientDoc
from app.retrieval.vector_store import VectorStore
from sqlalchemy import select

DATA_DIR = os.getenv("DATA_DIR", "data")
INDEX_DIR = os.getenv("INDEX_DIR", "index")
SQLITE_PATH = os.getenv("SQLITE_PATH", f"{INDEX_DIR}/patients.sqlite3")

def load_json_records(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def detect_mrd(row: dict) -> str:
    for k in ["mrd_number", "MRD Number", "mrd", "MRD", "mrdNumber"]:
        v = row.get(k)
        if v not in (None, ""):
            return str(v).strip()
    return ""

def detect_html(row: dict) -> str:
    for k in ["description", "document", "raw_document", "html", "content"]:
        v = row.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # Some datasets may store under nested keys; keep simple for assessment.
    return str(row.get("description") or "")

def main():
    data_dir = Path(DATA_DIR)
    index_dir = Path(INDEX_DIR)
    index_dir.mkdir(parents=True, exist_ok=True)

    sql = SqlStore(SQLITE_PATH)

    json_files = sorted([p for p in data_dir.glob("*.json")])
    if not json_files:
        raise SystemExit(f"No JSON files found in {data_dir.resolve()}")

    inserted = 0
    for jp in json_files:
        rows = load_json_records(jp)
        for r in rows:
            mrd = detect_mrd(r)
            if not mrd:
                continue
            html = detect_html(r)
            clean = html_to_text(html)

            doc_row = {
                "mrd_number": mrd,
                "patient_id": r.get("patient_id"),
                "visit_id": r.get("visit_id"),
                "visit_type": r.get("visit_type"),
                "visit_code": r.get("visit_code"),
                "adm_date": r.get("adm_date"),
                "dschg_date": r.get("dschg_date"),
                "document_type": r.get("document_type"),
                "form_name": r.get("form_name"),
                "doctor_name": r.get("doctor_name"),
                "doctor_speciality": r.get("doctor_speciality"),
                "gender": r.get("gender"),
                "raw_description_html": html,
                "clean_text": clean,
            }
            sql.insert_docs([doc_row])
            inserted += 1

    # Build vector chunks from SQL docs (ensures doc_id exists)
    with sql.SessionLocal() as s:
        all_docs = s.execute(select(PatientDoc)).scalars().all()

    items = []
    for d in all_docs:
        # Skip empty / unsupported doc types (if any)
        if not (d.clean_text or "").strip():
            continue
        for chunk in chunk_text(d.clean_text):
            items.append({
                "text": chunk,
                "mrd_number": d.mrd_number,
                "doc_id": d.id,
                "visit_id": d.visit_id,
                "document_type": d.document_type,
                "form_name": d.form_name,
                "adm_date": d.adm_date,
                "dschg_date": d.dschg_date,
                "doctor_speciality": d.doctor_speciality,
            })

    vs = VectorStore(
        index_path=str(index_dir / "faiss.index"),
        meta_path=str(index_dir / "faiss_meta.json"),
    )
    vs.build(items)

    print(f"Inserted rows: {inserted}")
    print(f"SQLite: {SQLITE_PATH}")
    print(f"FAISS chunks indexed: {len(items)}")
    print(f"FAISS index: {index_dir/'faiss.index'}")

if __name__ == "__main__":
    main()
