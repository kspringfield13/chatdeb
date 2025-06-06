import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the “kydxbot” package directory
package_dir = Path(__file__).parent       # this is C:\Users\kspri\Dev\kydxbot
dotenv_path = package_dir / ".env"
load_dotenv(dotenv_path=dotenv_path)

from .chatbot import handle_query, clear_conversation, summarize_conversation
from .visualize import generate_context_questions, create_matplotlib_visual

app = FastAPI(title="KYDxBot API")

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


class SummarizeRequest(BaseModel):
    history: list[dict]
    visuals: list[str] | None = None


class SummarizeResponse(BaseModel):
    summary: str

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


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest):
    try:
        text = summarize_conversation(req.history, req.visuals)
        return SummarizeResponse(summary=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear_history")
async def clear_history():
    """
    Optional: allows React frontend to reset conversation memory if needed.
    """
    clear_conversation()
    return {"status": "cleared"}

# If you want to run via "python server.py"
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
