# chatbot.py

import os, datetime
import numpy as np
from .db import get_engine
from .pinecone_utils import get_embedding, index
from sqlalchemy import text
from typing import List, Tuple
import re, math, json
from openai import OpenAI
from pathlib import Path

VISION_METADATA_FILE = Path(__file__).parent / "data" / "metadata.json"

def _load_metadata() -> dict:
    if VISION_METADATA_FILE.exists():
        try:
            with open(VISION_METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # noqa: BLE001
            print("metadata load error", e)
    return {}

VISION_METADATA = _load_metadata()

def _metadata_summary(meta: dict) -> str:
    lines = []
    for name, info in meta.items():
        cols = ", ".join(info.get("headers", [])[:5])
        summary = info.get("summary", "")
        piece = f"{name}: columns {cols}. {summary}".strip()
        lines.append(piece)
    return "\n".join(lines)

METADATA_SUMMARY = _metadata_summary(VISION_METADATA)

try:
    from dotenv import load_dotenv
    package_dir = Path(__file__).parent
    dotenv_file = package_dir / ".env"
    load_dotenv(dotenv_path=dotenv_file)
except Exception:
    # If python-dotenv isn't installed or .env is missing,
    # continue without loading environment variables
    load_dotenv = lambda *a, **kw: None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def call_openai_fallback(user_question: str) -> str:
    """
    If SQL or Pinecone fails, fall back to a direct OpenAI completion
    using the classic completions.create(...) endpoint.
    """
    try:
        client = OpenAI()

        system_msg = "You are a helpful assistant."
        if METADATA_SUMMARY:
            system_msg += "\nHere is data the user provided:\n" + METADATA_SUMMARY

        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_question},
            ],
        )

        # Extract the text portion of the first choice
        reply = completion.choices[0].message.content.strip()
        return reply

    except Exception as e:
        print(f"⚠️ OpenAI fallback error: {e}")
        return "Sorry, I’m having trouble right now. Please try again later."

def extract_limit_from_question(q: str) -> int | None:
    """
    Simple regex to find a leading number in the question.
    e.g. "Which 5 customers have the highest sales?" → 5
         "Top 10 X by Y" → 10
    """
    m = re.search(r"\btop\s+(\d+)\b|\bwhich\s+(\d+)\b", q, flags=re.IGNORECASE)
    if m:
        # the regex has two capture groups; only one will be non‐None
        return int(m.group(1) or m.group(2))
    return None

def is_data_question(query_text: str) -> bool:
    """Return ``True`` if a question is data‑centric.

    A query is considered *data‑centric* when the user is clearly looking for
    numbers, lists or metrics that can be answered from the database.  Typical
    examples for small/medium business owners include:

    - "How many orders did we ship last month?"
    - "Show me the top 10 customers by revenue."
    - "What's the average order value?"
    - "List employees with more than 5 sales this quarter."

    When such keywords appear, the question is routed through the SQLAgent
    chain (LangChain → DuckDB) rather than the semantic search fallback.
    """

    q = query_text.lower()
    data_keywords = [
        "average", "sum(", "count(", "how many", "what is", "list",
        "top", "highest", "lowest", "per", "between", "profit",
        "sales", "customers", "products", "revenue", "orders",
        "invoices", "inventory", "expenses", "transactions", "employees",
        "payroll", "income", "metrics",
        # Consider references to generic data or database terms
        "database", "duckdb", "dataset", "datasets", "db",
        "loaded data", "imported data", "shared data", "the data",
    ]
    return any(kw in q for kw in data_keywords)

def handle_semantic_search(query_text: str, top_k: int = 3) -> str:
    """
    1) Embed the query  
    2) Query Pinecone → top_k matches  
    3) If ID starts with 'cust_' → fetch that customer row via SQLAlchemy engine  
    4) If ID starts with 'prod_' → fetch that product row via SQLAlchemy engine  
    5) Return a plain‐text summary (one line per match)
    """
    # ── 1) Compute the embedding vector for query_text ─────────────────────────────
    q_emb = get_embedding(query_text)
    
    if hasattr(q_emb, "tolist"):
        q_emb = q_emb.tolist()

    # 2) Print length & types
    print(f">>> q_emb length = {len(q_emb)}")
    for i, x in enumerate(q_emb[:5]):
        print(f">>> q_emb[{i}] = {x} ({type(x)})")

    # 3) Check NaN/Inf
    bad = [i for i, x in enumerate(q_emb) if isinstance(x, float) and (math.isnan(x) or math.isinf(x))]
    if bad:
        print(f">>> Found invalid entries (NaN/Inf) at indices: {bad[:10]} …")

    # 4) Cast to float
    try:
        q_emb = [float(x) for x in q_emb]
        print(">>> Cast to Python floats succeeded.")
    except Exception as e:
        print(">>> Cast to Python floats failed:", e)

    # 5) Check dimension
    EXPECTED_DIM = 1536
    if len(q_emb) != EXPECTED_DIM:
        print(f">>> DIM MISMATCH: {len(q_emb)} vs {EXPECTED_DIM}")

    # 6) Test JSON serialization
    try:
        temp = json.dumps({"queries": [q_emb], "top_k": 3})
        print(">>> JSON serialization OK.")
    except Exception as e:
        print(">>> JSON serialization failed:", e)

    # 7) Finally query Pinecone
    response = index.query(queries=[q_emb], top_k=top_k, include_metadata=True)
    matches = getattr(response, "matches", None) or response.get("matches", [])

    if not matches:
        return "No relevant customers or products found."

    # ── 3) Obtain the SQLAlchemy engine once ──────────────────────────────────────
    ENGINE = get_engine()

    # ── 4) For each Pinecone match, look up details via ENGINE ──────────────────
    lines: List[str] = []
    for m in matches:
        mid = m.id
        score = getattr(m, "score", m.get("score", 0.0))

        # --- 4a) Customer IDs begin with 'cust_' → look up in `customers` table
        if mid.startswith("cust_"):
            try:
                user_id = int(mid.split("_", 1)[1])
            except ValueError:
                meta = m.metadata or m.get("metadata", {})
                lines.append(f"Unparsable customer ID='{mid}', metadata: {meta}")
                continue

            sql = text("""
                SELECT 
                    user_id,
                    customer_first_name,
                    customer_last_name,
                    num_orders_Cancelled,
                    num_orders_Returned,
                    num_web_sessions
                FROM customers
                WHERE user_id = :uid
            """)
            with ENGINE.connect() as conn:
                result = conn.execute(sql, {"uid": user_id}).fetchone()

            if result:
                uid, first, last, cancelled, returned, sessions = result
                lines.append(
                    f"Customer {first} {last} (ID {uid}): "
                    f"cancelled={cancelled}, returned={returned}, sessions={sessions} "
                    f"(score={score:.3f})"
                )
            else:
                lines.append(f"Customer ID {user_id} not found (score={score:.3f})")

        # --- 4b) Product IDs begin with 'prod_' → look up in `products` table
        elif mid.startswith("prod_"):
            try:
                product_id = int(mid.split("_", 1)[1])
            except ValueError:
                meta = m.metadata or m.get("metadata", {})
                lines.append(f"Unparsable product ID='{mid}', metadata: {meta}")
                continue

            sql = text("""
                SELECT 
                    product_id,
                    product_name,
                    product_category,
                    sales_amount,
                    cost_of_goods_sold,
                    profit
                FROM products
                WHERE product_id = :pid
            """)
            with ENGINE.connect() as conn:
                result = conn.execute(sql, {"pid": product_id}).fetchone()

            if result:
                pid, name, category, sales, cogs, profit = result
                lines.append(
                    f"Product '{name}' (ID {pid}), category={category}, "
                    f"sales=${sales:,.2f}, COGS=${cogs:,.2f}, profit=${profit:,.2f} "
                    f"(score={score:.3f})"
                )
            else:
                lines.append(f"Product ID {product_id} not found (score={score:.3f})")

        elif mid.startswith("dc_"):
            try:
                dc_id = int(mid.split("_", 1)[1])
            except ValueError:
                meta = m.metadata or m.get("metadata", {})
                lines.append(f"Unparsable distribution center ID='{mid}', metadata: {meta}")
                continue

            sql = text("""
                SELECT
                    distribution_center_id,
                    distribution_center_name,
                    items_in_stock,
                    total_sales,
                    total_inventory_cost
                FROM distribution_center_inventory
                WHERE distribution_center_id = :dcid
            """)
            with ENGINE.connect() as conn:
                result = conn.execute(sql, {"dcid": dc_id}).fetchone()

            if result:
                did, name, stock, sales, inv_cost = result
                lines.append(
                    f"Center '{name}' (ID {did}): stock={stock}, sales=${sales:,.2f}, cost=${inv_cost:,.2f} "
                    f"(score={score:.3f})"
                )
            else:
                lines.append(f"Distribution center ID {dc_id} not found (score={score:.3f})")
                
        # --- 4c) Fallback if Pinecone returns an unexpected ID format
        else:
            meta = m.metadata if hasattr(m, "metadata") else m.get("metadata", {})
            lines.append(f"(Match ID={mid}, score={score:.3f}, metadata={meta})")

    # ── 5) Join all lines into a single multi-line string ─────────────────────────
    return "\n".join(lines)

def format_zero_rows() -> str:
    return "No records found."

def _format_generic_row(row: Tuple) -> str:
    """Format an arbitrary tuple of values safely."""
    parts = []
    for val in row:
        if isinstance(val, int):
            parts.append(str(val))
        elif isinstance(val, float):
            parts.append(f"{val:,.2f}")
        else:
            try:
                num = float(val)
                parts.append(f"{num:,.2f}")
            except Exception:
                parts.append(str(val))
    return " — ".join(parts)


def format_single_row(row: Tuple) -> str:
    """
    Format a single SQL result row for display.

    When ``row`` matches the expected customer or product shapes it is formatted
    using those conventions.  Otherwise the values are joined generically which
    avoids type-related formatting errors.
    """

    if len(row) == 4 and isinstance(row[3], (int, float)):
        # Customer format
        _, first, last, total = row
        return f"{first} {last} — {total:,.2f}"
    if len(row) == 3 and isinstance(row[2], (int, float)):
        # Product format
        name, category, sales = row
        return f"{name} ({category}) — {sales:,.2f}"

    return _format_generic_row(row)

def format_numbered_list(rows: List[Tuple]) -> str:
    """
    2–5 customers. Each row is (id, first, last, total).
    We reuse format_single_row_customer but add numbering.
    """
    lines = []
    for i, row in enumerate(rows, start=1):
        single = format_single_row(row)
        lines.append(f"{i}. {single}  ")
    return "\n".join(lines)

def format_markdown_table(
    rows: list[tuple],
    limit: int | None = None,
) -> str:
    """Return a ``TABLE:`` prefixed path to a table image generated from the data."""

    from .visualize import create_table_visual

    if not rows:
        return "_No data returned._"

    path = create_table_visual(rows, limit)
    if not path:
        return "_No data returned._"

    return f"TABLE:{path}"
    
def _save_to_history(query: str, response: str, confidence: float | None):
    """
    Appends a new chat entry into chatbot_responses.json.
    Format of each entry:
      {
        "query_text": "...",
        "retrieved_response": "...",
        "timestamp": "YYYY-MM-DDTHH:MM:SS",
        "confidence_score": float or null
      }
    """
    record = {
        "query_text": query,
        "retrieved_response": response,
        "timestamp": datetime.datetime.now().isoformat(),
        "confidence_score": confidence
    }

    fname = "chatbot_responses.json"
    try:
        # 1) If the file exists and has valid JSON, load it; otherwise start with []
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        else:
            data = []
    except Exception:
        # If JSON is malformed or any I/O error, overwrite with a fresh list
        data = []

    # 2) Append the new record
    data.append(record)

    # 3) Write back out to disk (pretty-print)
    try:
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Couldn’t write to {fname}: {e}")

def handle_query(query_text: str) -> str:
    q = query_text.strip()
    if not q:
        return "Please type a question."

    if is_data_question(q):
        try:
            from .langchain_sql import query_via_sqlagent
            rows = query_via_sqlagent(q)
            n = len(rows)

            if n == 0:
                reply = format_zero_rows()
                _save_to_history(q, reply, confidence=None)
                return reply

            if n == 1:
                reply = format_single_row(rows[0])
                _save_to_history(q, reply, confidence=None)
                return reply

            if 2 <= n <= 5:
                body = format_numbered_list(rows)
                reply = body
                _save_to_history(q, reply, confidence=None)
                return reply

            reply = format_markdown_table(rows, limit=None)
            _save_to_history(q, reply, confidence=None)
            return reply

        except Exception as e:
            # Any error in SQLAgent / formatting → open AI fallback
            print("⚠️ Data‐centric error:", e)
            reply = call_openai_fallback(q)
            _save_to_history(q, reply, confidence=None)
            return reply
        
    try:
        reply = handle_semantic_search(q, top_k=3)
        _save_to_history(q, reply, confidence=None)
        return reply
    except Exception as e:
        # Any error in semantic‐search → open AI fallback
        print("⚠️ Semantic‐search error:", e)
        reply = call_openai_fallback(q)
        _save_to_history(q, reply, confidence=None)
        return reply

def clear_conversation():
    """Reset any conversation state (currently no-op)."""
    pass


def _aggregate_metrics() -> dict:
    """Build simple aggregate metrics using DuckDB."""
    try:
        import duckdb
    except Exception:
        return {}

    db_path = Path("data/data.db")
    if not db_path.exists():
        return {}

    con = duckdb.connect(str(db_path))
    metrics = {}
    try:
        metrics["customer_count"] = con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        metrics["product_count"] = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        metrics["total_sales"] = con.execute("SELECT SUM(sales_amount) FROM products").fetchone()[0] or 0
    except Exception:
        return {}
    finally:
        con.close()
    return metrics


def summarize_history() -> str:
    """Return a text summary of recent chat history and data aggregates."""

    history_path = Path("chatbot_responses.json")
    if history_path.exists():
        try:
            data = json.loads(history_path.read_text())
        except Exception:
            data = []
    else:
        data = []

    last_entries = data[-5:]
    lines = ["Recent conversation:"]
    for entry in last_entries:
        q = entry.get("query_text", "").strip()
        r = entry.get("retrieved_response", "").strip()
        lines.append(f"- Q: {q}\n  A: {r}")

    metrics = _aggregate_metrics()
    if metrics:
        lines.append("\nData overview (edit logic if needed):")
        for k, v in metrics.items():
            if isinstance(v, float):
                lines.append(f"- {k.replace('_', ' ').title()}: {v:,.2f}")
            else:
                lines.append(f"- {k.replace('_', ' ').title()}: {v}")
        lines.append("\nContinue with these aggregates? Adjust logic if needed.")

    return "\n".join(lines)
    """
    If you have any global state to clear, do it here.
    (Currently, none is needed, but this stub satisfies the /clear_history endpoint.)
    """
    pass


def get_intro_message() -> str:
    """Return a short greeting referencing the extracted data."""
    if not METADATA_SUMMARY:
        return ""
    return (
        "Here is what I found in your data files:\n"
        f"{METADATA_SUMMARY}\n"
        "Is this the information you'd like to analyze?"
    )


def summarize_conversation(history: list[dict], visuals: list[str] | None = None) -> str:
    """Return a short text summary of the conversation history.

    ``history`` should be a list of objects with ``sender`` and ``text`` keys.
    Any chart URLs passed via ``visuals`` will be included at the end of the
    summary.
    """

    messages = []
    for entry in history:
        role = "user" if entry.get("sender") == "user" else "assistant"
        text = entry.get("text", "")
        messages.append({"role": role, "content": text})

    if visuals:
        desc = "\n".join(f"Chart created: {url}" for url in visuals)
        messages.append({"role": "assistant", "content": desc})

    system_prompt = (
        "Provide a concise bullet-point recap of the conversation. "
        "Highlight any data mentioned and reference charts or visuals that were created."
    )

    try:
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "system", "content": system_prompt}] + messages,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:  # noqa: BLE001
        print("summarize_conversation error", e)
        return "Sorry, I couldn't generate a summary."
