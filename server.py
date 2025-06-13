import os
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from .config import CHARTS_DIR, UPLOAD_DIR, UPLOAD_DB_PATH

from .chatbot import (
    handle_query,
    clear_conversation,
    summarize_conversation,
    get_intro_message,
)
from .visualize import (
    generate_context_questions,
    create_matplotlib_visual,
    create_visual_with_fallback,
)
from .infograph import generate_infograph_questions, create_infographic
from .erd import generate_erd, get_data_summary, describe_erd
from .chatbot import _maybe_convert_text_table
from .directorscut import generate_directors_cut
from .db import DEFAULT_DB_PATH

app = FastAPI(title="KYDxBot API")

# Serve generated chart and table images
CHARTS_DIR.mkdir(exist_ok=True)
app.mount("/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")

# 1) Define which origins are allowed to talk to this API.
#    If you’re in development, you might allow just localhost:3000.
origins = [
    "http://localhost:3000",  # if you ever ran on 3000
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",  # optional, sometimes helpful
]

# 2) Add middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # ← which domains can send requests
    allow_credentials=True,           # allow cookies, Authorization headers, etc.
    allow_methods=["*"],              # allow all HTTP methods: GET, POST, etc.
    allow_headers=["*"],              # allow all headers like Content-Type
)

# (Then your existing endpoint definitions come below)
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str


class VizQuestionsRequest(BaseModel):
    history: list[dict]


class VizQuestionsResponse(BaseModel):
    questions: list[str]


class VizCompleteRequest(BaseModel):
    history: list[dict]
    answers: list[str]


class VizCompleteResponse(BaseModel):
    chart_url: str | None


class InfographQuestionsRequest(BaseModel):
    history: list[dict]


class InfographQuestionsResponse(BaseModel):
    questions: list[str]


class InfographCompleteRequest(BaseModel):
    history: list[dict]
    answers: list[str]


class InfographCompleteResponse(BaseModel):
    image_url: str | None


class SummarizeRequest(BaseModel):
    history: list[dict]
    visuals: list[str] | None = None


class SummarizeResponse(BaseModel):
    summary: str


class MyDataResponse(BaseModel):
    summary: str
    erd_url: str | None = None
    erd_desc: str | None = None
    tables: list[str] | None = None


class DBInfoResponse(BaseModel):
    size: int


class DirectorsCutRequest(BaseModel):
    history: list[dict]


class DirectorsCutResponse(BaseModel):
    video_url: str | None = None


class UploadResponse(BaseModel):
    status: str


class IntroResponse(BaseModel):
    message: str


@app.get("/intro", response_model=IntroResponse)
async def intro():
    msg = get_intro_message()
    return IntroResponse(message=msg)


@app.post("/upload_data", response_model=UploadResponse)
async def upload_data(files: list[UploadFile] = File(...)):
    """Save uploaded files and ingest them into a temporary DuckDB database."""
    UPLOAD_DIR.mkdir(exist_ok=True)
    total = 0
    saved = []
    for file in files:
        data = await file.read()
        total += len(data)
        if total > 1024 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Upload limit exceeded")
        path = UPLOAD_DIR / file.filename
        with open(path, "wb") as f:
            f.write(data)
        saved.append(path)

    import pandas as pd
    import duckdb

    con = duckdb.connect(str(UPLOAD_DB_PATH))
    for path in saved:
        name = path.stem
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        elif path.suffix.lower() in {".xls", ".xlsx"}:
            df = pd.read_excel(path)
        elif path.suffix.lower() == ".json":
            df = pd.read_json(path, orient="records", lines=False)
        else:
            continue
        con.execute(f'DROP TABLE IF EXISTS "{name}";')
        con.register("tmp_df", df)
        con.execute(f'CREATE TABLE "{name}" AS SELECT * FROM tmp_df;')
        con.unregister("tmp_df")
    con.close()

    os.environ["DUCKDB_PATH"] = str(UPLOAD_DB_PATH)
    os.environ["DBT_DUCKDB_PATH"] = str(UPLOAD_DB_PATH)
    return UploadResponse(status="ok")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Receives JSON: { "query": "How do I reset my password?" }
    Returns JSON: { "response": "..."}
    """

    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    response_text = handle_query(user_query)
    return ChatResponse(response=response_text)


@app.post("/visualize/questions", response_model=VizQuestionsResponse)
async def viz_questions(req: VizQuestionsRequest):
    try:
        qs = generate_context_questions(req.history)
        return VizQuestionsResponse(questions=qs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/visualize/complete", response_model=VizCompleteResponse)
async def viz_complete(req: VizCompleteRequest):
    try:
        url = create_visual_with_fallback(req.answers, req.history)
        url = f"/charts/{Path(url).name}"
        return VizCompleteResponse(chart_url=url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/infograph/questions", response_model=InfographQuestionsResponse)
async def infograph_questions(req: InfographQuestionsRequest):
    try:
        qs = generate_infograph_questions(req.history)
        return InfographQuestionsResponse(questions=qs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/infograph/complete", response_model=InfographCompleteResponse)
async def infograph_complete(req: InfographCompleteRequest):
    try:
        url = create_infographic(req.answers)
        url = f"/charts/{Path(url).name}"
        return InfographCompleteResponse(image_url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest):
    try:
        text = summarize_conversation(req.history, req.visuals)
        return SummarizeResponse(summary=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/db_info", response_model=DBInfoResponse)
async def db_info():
    """Return basic information about the DuckDB database."""
    try:
        path = os.getenv("DUCKDB_PATH", str(DEFAULT_DB_PATH))
        size = os.path.getsize(path)
    except Exception as exc:  # noqa: BLE001
        print("getsize error", exc)
        size = 0
    return DBInfoResponse(size=size)


@app.get("/my_data", response_model=MyDataResponse)
async def my_data():
    """Return a brief summary of the DuckDB data and an ER diagram image.

    Any errors when generating the summary or diagram should not result in a
    500 response so that the frontend can still display whatever information was
    successfully gathered. This mirrors the more forgiving behaviour used by the
    generic ``/summarize`` endpoint.
    """

    summary: str | None = ""
    url = None
    desc = None
    tables: list[str] | None = None

    try:
        summary_text = get_data_summary()
        lines = summary_text.splitlines()[2:]
        tables = []
        for l in lines:
            parts = [p.strip() for p in l.split("|") if p.strip()]
            if len(parts) >= 2:
                tables.append(parts[0])
        summary = _maybe_convert_text_table(summary_text)
    except Exception as exc:  # noqa: BLE001
        print("get_data_summary error", exc)

    try:
        url = generate_erd()
    except Exception as exc:  # noqa: BLE001
        print("generate_erd error", exc)
        url = None

    if url:
        try:
            desc = describe_erd(url)
        except Exception as exc:  # noqa: BLE001
            print("describe_erd error", exc)
            desc = None
        url = f"/charts/{Path(url).name}"

    return MyDataResponse(summary=summary, erd_url=url, erd_desc=desc, tables=tables)


@app.post("/directors_cut", response_model=DirectorsCutResponse)
async def directors_cut(req: DirectorsCutRequest):
    try:
        url = generate_directors_cut(req.history)
        url = f"/charts/{Path(url).name}"
        return DirectorsCutResponse(video_url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear_history")
async def clear_history():
    """
    Optional: allows React frontend to reset conversation memory if needed.
    """
    clear_conversation()
    return {"status": "cleared"}


class SummaryResponse(BaseModel):
    summary: str


@app.get("/summarize", response_model=SummaryResponse)
async def summarize():
    """Return a short summary of recent chat activity and data."""
    text = summarize_history()
    return SummaryResponse(summary=text)

# If you want to run via "python server.py"
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
