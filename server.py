import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the “kydxbot” package directory
package_dir = Path(__file__).parent       # this is C:\Users\kspri\Dev\kydxbot
dotenv_path = package_dir / ".env"
load_dotenv(dotenv_path=dotenv_path)

from .chatbot import (
    handle_query,
    clear_conversation,
    summarize_conversation,
    get_intro_message,
)
from .visualize import generate_context_questions, create_matplotlib_visual
from .infograph import generate_infograph_questions, create_infographic
from .erd import generate_erd, get_data_summary, describe_erd

app = FastAPI(title="KYDxBot API")

# Serve generated chart and table images
charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)
app.mount("/charts", StaticFiles(directory=str(charts_dir)), name="charts")

# 1) Define which origins are allowed to talk to this API.
#    If you’re in development, you might allow just localhost:3000.
origins = [
    "http://localhost:3000",
    # You could also add "http://127.0.0.1:3000" or any deployed domain later.
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


class IntroResponse(BaseModel):
    message: str


@app.get("/intro", response_model=IntroResponse)
async def intro():
    msg = get_intro_message()
    return IntroResponse(message=msg)

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
        url = create_matplotlib_visual(req.answers)
        return VizCompleteResponse(chart_url=url)
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


@app.get("/my_data", response_model=MyDataResponse)
async def my_data():
    """Return a brief summary of the DuckDB data and an ER diagram image."""
    try:
        summary = get_data_summary()
        url = generate_erd()
        desc = describe_erd(url)
        return MyDataResponse(summary=summary, erd_url=url, erd_desc=desc)
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
