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

from .chatbot import handle_query, clear_conversation, summarize_history

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
