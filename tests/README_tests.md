Manual  tests (assessment-friendly):
1) /health returns 200
2) /query with invalid MRD returns 404 + structured error
3) /query with empty query returns 400
4) /query count question returns 200 without needing LLM
5) /query semantic question returns answer + confidence
