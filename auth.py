import os
import secrets
import smtplib
from email.mime.text import MIMEText
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
                    email TEXT PRIMARY KEY,
                    password_hash TEXT,
                    verified INTEGER DEFAULT 0,
                    verification_token TEXT
                )
                """
            )
        )


def _hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()


def create_user(email: str, password: str) -> str:
    engine = get_engine()
    hashed = _hash_password(password)
    token = secrets.token_urlsafe(16)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO user_credentials (email, password_hash, verification_token) VALUES (:e, :p, :t)"
            ),
            {"e": email, "p": hashed, "t": token},
        )
    return token


def verify_user(email: str, password: str) -> bool:
    engine = get_engine()
    hashed = _hash_password(password)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT password_hash, verified FROM user_credentials WHERE email=:e"
            ),
            {"e": email},
        ).fetchone()
    return row is not None and row[0] == hashed and row[1] == 1


def issue_token(username: str) -> str:
    token = secrets.token_urlsafe(32)
    _tokens[token] = username
    return token


def get_username(token: str) -> str | None:
    return _tokens.get(token)


def mark_verified(token: str) -> str | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "UPDATE user_credentials SET verified=1 WHERE verification_token=:t RETURNING email"
            ),
            {"t": token},
        ).fetchone()
    return row[0] if row else None


def send_verification_email(email: str, token: str) -> None:
    user = os.getenv("GMAIL_USERNAME")
    pw = os.getenv("GMAIL_PASSWORD")
    if not user or not pw:
        print("Email credentials missing; skipping verification email")
        return
    link = f"http://localhost:3000/verify?token={token}"
    msg = MIMEText(
        f"<p>Click the button below to verify your password:</p><p><a href='{link}'>Verify</a></p>",
        "html",
    )
    msg["Subject"] = "Verify your KYDxBot account"
    msg["From"] = user
    msg["To"] = email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.sendmail(user, [email], msg.as_string())
