import re
from bs4 import BeautifulSoup

_whitespace_re = re.compile(r"\s+")

def html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator="\n")
    text = text.replace("\r", "\n")
    text = _whitespace_re.sub(" ", text).strip()
    return text

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u00a0", " ")
    s = _whitespace_re.sub(" ", s).strip()
    return s

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks
