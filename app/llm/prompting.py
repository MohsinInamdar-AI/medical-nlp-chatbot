def build_prompt(query: str, facts: dict, contexts: list[dict]) -> str:
    facts_block = ""
    if facts:
        parts = []
        for k, v in facts.items():
            if v:
                parts.append(f"- {k}: {v}")
        if parts:
            facts_block = "STRUCTURED FACTS (from records):\n" + "\n".join(parts) + "\n\n"

    ctx_lines = []
    for c in contexts:
        meta = f"MRD={c.get('mrd_number')} doc_id={c.get('doc_id')} form={c.get('form_name')} type={c.get('document_type')} date={c.get('dschg_date') or c.get('adm_date')}"
        ctx_lines.append(f"[CONTEXT]\n{meta}\n{c.get('text')}\n")
    ctx_block = "\n".join(ctx_lines).strip()

    return f"""You are a clinical documentation assistant.
You must answer ONLY using the provided patient record excerpts and structured facts.

Rules (MANDATORY):
- Clinical tone only.
- No assumptions, no speculation.
- Do not add medical knowledge not present in the excerpts.
- If the answer is not explicitly present, say exactly:
  "No relevant information found in the patient's records."
- Keep the answer concise (1-6 sentences), unless the user asks for a list or count.

{facts_block}PATIENT RECORD EXCERPTS:
{ctx_block}

QUESTION:
{query}

ANSWER (clinical, grounded, no speculation):
""".strip()
