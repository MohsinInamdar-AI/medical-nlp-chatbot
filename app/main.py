from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes import router

app = FastAPI(
    title="Medical NLP Chatbot API",
    version="1.0.0",
    description="Hybrid retrieval (SQLite + FAISS RAG) with local LLM (Ollama).",
)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Let FastAPI handle HTTPException normally (it is a subclass of Exception but has its own handler)
    # Only catch unexpected errors.
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=500, content={"error": "Internal server error", "code": "INTERNAL_ERROR"})

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}
