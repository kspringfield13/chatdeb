import os
import uvicorn
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import handle_query, clear_conversation
from auth import (
    init_user_table,
    create_user,
    verify_user,
    issue_token,
    get_username,
)

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

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


class AuthRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(AuthRequest):
    secret: str


class TokenResponse(BaseModel):
    token: str


@app.post("/register")
async def register(auth: RegisterRequest):
    if not auth.username.strip() or not auth.password:
        raise HTTPException(status_code=400, detail="Username and password required")
    if SECRET_KEY is None:
        raise HTTPException(status_code=500, detail="Server missing SECRET_KEY")
    attempts = _register_attempts.get(auth.username, 0)
    if attempts >= 5:
        raise HTTPException(
            status_code=403,
            detail=(
                "Too many attempts. Please reach out to kydxbot@support.com to retrieve the SECRET_KEY if you are actively subscribed."
            ),
        )
    if auth.secret != SECRET_KEY:
        attempts += 1
        _register_attempts[auth.username] = attempts
        if attempts >= 5:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Too many attempts. Please reach out to kydxbot@support.com to retrieve the SECRET_KEY if you are actively subscribed."
                ),
            )
        raise HTTPException(status_code=401, detail="Invalid secret code")

    _register_attempts.pop(auth.username, None)
    try:
        create_user(auth.username, auth.password)
    except Exception:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"status": "registered"}


@app.post("/login", response_model=TokenResponse)
async def login(auth: AuthRequest):
    if not auth.username.strip() or not auth.password:
        raise HTTPException(status_code=400, detail="Username and password required")
    if not verify_user(auth.username, auth.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = issue_token(auth.username)
    return TokenResponse(token=token)


@app.get("/me")
async def read_me(x_token: str = Header(...)):
    username = get_username(x_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"username": username}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, x_token: str = Header(...)):
    """
    Receives JSON: { "query": "How do I reset my password?" }
    Returns JSON: { "response": "..."}
    """
    username = get_username(x_token)
    if not username:
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
