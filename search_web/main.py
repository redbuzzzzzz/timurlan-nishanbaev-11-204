from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from vector_search.engine import VectorSearchEngine

app = FastAPI(title="Vector Search")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
engine = VectorSearchEngine()


@app.get("/", response_class=HTMLResponse)
def index(request: Request, q: str = Query(default="")) -> HTMLResponse:
    hits = []
    message = ""
    normalized_query = ""
    if q:
        result = engine.search(q, top_k=10)
        hits = result.hits
        message = result.message
        normalized_query = result.normalized_query

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "query": q,
            "normalized_query": normalized_query,
            "hits": hits,
            "message": message,
        },
    )

