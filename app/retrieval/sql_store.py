from __future__ import annotations
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index, select, func
from sqlalchemy.orm import declarative_base, sessionmaker
from dataclasses import dataclass
from typing import Iterable

Base = declarative_base()

class PatientDoc(Base):
    __tablename__ = "patient_docs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mrd_number = Column(String, index=True, nullable=False)

    patient_id = Column(Integer, nullable=True)
    visit_id = Column(String, nullable=True)
    visit_type = Column(String, nullable=True)
    visit_code = Column(String, nullable=True)
    adm_date = Column(String, nullable=True)
    dschg_date = Column(String, nullable=True)

    document_type = Column(String, nullable=True)
    form_name = Column(String, nullable=True)

    doctor_name = Column(String, nullable=True)
    doctor_speciality = Column(String, nullable=True)
    gender = Column(String, nullable=True)

    raw_description_html = Column(Text, nullable=True)
    clean_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

Index("ix_patient_docs_mrd_visit", PatientDoc.mrd_number, PatientDoc.visit_id)

@dataclass
class SqlStore:
    sqlite_path: str

    def __post_init__(self):
        self.engine = create_engine(f"sqlite:///{self.sqlite_path}", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)

    def insert_docs(self, docs: Iterable[dict]):
        with self.SessionLocal() as s:
            for d in docs:
                s.add(PatientDoc(**d))
            s.commit()

    def mrd_exists(self, mrd_number: str) -> bool:
        with self.SessionLocal() as s:
            row = s.execute(select(PatientDoc.id).where(PatientDoc.mrd_number == mrd_number).limit(1)).first()
            return row is not None

    def quick_facts(self, mrd_number: str) -> dict:
        with self.SessionLocal() as s:
            rows = s.execute(select(PatientDoc).where(PatientDoc.mrd_number == mrd_number)).scalars().all()
        if not rows:
            return {}
        def first_nonempty(attr: str):
            for r in rows:
                v = getattr(r, attr, None)
                if v not in (None, "", "null"):
                    return str(v)
            return None
        return {"patient_id": first_nonempty("patient_id"), "gender": first_nonempty("gender")}

    def count_documents(self, mrd_number: str) -> int:
        with self.SessionLocal() as s:
            return int(s.execute(select(func.count()).select_from(PatientDoc).where(PatientDoc.mrd_number == mrd_number)).scalar_one())

    def count_visits(self, mrd_number: str) -> int:
        with self.SessionLocal() as s:
            # distinct visit_id
            return int(s.execute(select(func.count(func.distinct(PatientDoc.visit_id))).where(PatientDoc.mrd_number == mrd_number)).scalar_one())

    def count_by_document_type(self, mrd_number: str) -> list[tuple[str, int]]:
        with self.SessionLocal() as s:
            rows = s.execute(
                select(PatientDoc.document_type, func.count())
                .where(PatientDoc.mrd_number == mrd_number)
                .group_by(PatientDoc.document_type)
                .order_by(func.count().desc())
            ).all()
        out = []
        for dt, c in rows:
            out.append((dt or "Unknown", int(c)))
        return out
