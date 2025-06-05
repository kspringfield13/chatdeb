import os
import uvicorn
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import handle_query, clear_conversation
from auth import (
    init_user_table,
    create_user,
    verify_user,
    issue_token,
    get_username,
    mark_verified,
    send_verification_email,
)
from google.oauth2 import id_token
from google.auth.transport import requests

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

_register_attempts: dict[str, int] = {}

app = FastAPI(title="SupportyxBot API")


@app.on_event("startup")
def _startup() -> None:
    init_user_table()

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


class GoogleAuth(BaseModel):
    token: str
    password: str


class RegisterRequest(GoogleAuth):
    secret: str


class TokenResponse(BaseModel):
    token: str


def _get_email(id_token_str: str) -> str | None:
    if not GOOGLE_CLIENT_ID:
        return None
    try:
        info = id_token.verify_oauth2_token(id_token_str, requests.Request(), GOOGLE_CLIENT_ID)
        return info.get("email")
    except Exception:
        return None


@app.post("/register")
async def register(auth: RegisterRequest, background_tasks: BackgroundTasks):
    if not auth.password:
        raise HTTPException(status_code=400, detail="Password required")
    if SECRET_KEY is None or not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Server missing configuration")
    email = _get_email(auth.token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    attempts = _register_attempts.get(email, 0)
    if attempts >= 5:
        raise HTTPException(
            status_code=403,
            detail=(
                "Too many attempts. Please reach out to kydxbot@support.com to retrieve the SECRET_KEY if you are actively subscribed."
            ),
        )
    if auth.secret != SECRET_KEY:
        attempts += 1
        _register_attempts[email] = attempts
        if attempts >= 5:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Too many attempts. Please reach out to kydxbot@support.com to retrieve the SECRET_KEY if you are actively subscribed."
                ),
            )
        raise HTTPException(status_code=401, detail="Invalid secret code")

    _register_attempts.pop(email, None)
    try:
        verify_token = create_user(email, auth.password)
    except Exception:
        raise HTTPException(status_code=400, detail="User already exists")
    background_tasks.add_task(send_verification_email, email, verify_token)
    return {"status": "registered"}


@app.post("/login", response_model=TokenResponse)
async def login(auth: GoogleAuth):
    if not auth.password:
        raise HTTPException(status_code=400, detail="Password required")
    email = _get_email(auth.token)
    if not email or not verify_user(email, auth.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = issue_token(email)
    return TokenResponse(token=token)


@app.get("/verify", response_model=TokenResponse)
async def verify_email(token: str):
    email = mark_verified(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    session = issue_token(email)
    return TokenResponse(token=session)


@app.get("/me")
async def read_me(x_token: str = Header(...)):
    user_email = get_username(x_token)
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"username": user_email}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, x_token: str = Header(...)):
    """
    Receives JSON: { "query": "How do I reset my password?" }
    Returns JSON: { "response": "..."}
    """
    user_email = get_username(x_token)
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")

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


# If you want to run via "python server.py"
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
