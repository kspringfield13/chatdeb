import os
import secrets
from hashlib import sha256
from sqlalchemy import text
from db import get_engine, DUCKDB_PATH

_tokens: dict[str, str] = {}


def init_user_table() -> None:
    """Ensure the user_credentials table exists."""
    os.makedirs(os.path.dirname(DUCKDB_PATH), exist_ok=True)
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS user_credentials (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT
                )
                """
            )
        )


def _hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()


def create_user(username: str, password: str) -> None:
    engine = get_engine()
    hashed = _hash_password(password)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO user_credentials (username, password_hash) VALUES (:u, :p)"
            ),
            {"u": username, "p": hashed},
        )


def verify_user(username: str, password: str) -> bool:
    engine = get_engine()
    hashed = _hash_password(password)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT password_hash FROM user_credentials WHERE username=:u"),
            {"u": username},
        ).fetchone()
    return row is not None and row[0] == hashed


def issue_token(username: str) -> str:
    token = secrets.token_urlsafe(32)
    _tokens[token] = username
    return token


def get_username(token: str) -> str | None:
    return _tokens.get(token)
