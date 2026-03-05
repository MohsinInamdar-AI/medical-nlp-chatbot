from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    mrd_number: str = Field(..., description="MRD Number / patient identifier (string)")
    query: str = Field(..., min_length=1, description="Clinical query")

class QueryResponse(BaseModel):
    mrd_number: str
    answer: str
    confidence: str

class ErrorDetail(BaseModel):
    error: str
    code: str
    mrd_number: str | None = None
