# langchain_sql.py

import os, ast
from pathlib import Path
try:
    from dotenv import load_dotenv
    package_dir = Path(__file__).parent
    dotenv_file = package_dir / ".env"
    load_dotenv(dotenv_path=dotenv_file)
except Exception:
    # If python-dotenv isn't installed or .env is missing,
    # continue without loading environment variables
    load_dotenv = lambda *a, **kw: None

# 1) LangChain imports
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from sqlalchemy import text

from .db import get_engine

# 2) Load environment variables (for OPENAI_API_KEY, if you haven't set it elsewhere)

ENGINE = get_engine()
db = SQLDatabase(
    ENGINE,
    schema="main",
    include_tables=[
        "customers",
        "products",
        "distribution_center_inventory",
    ],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your .env")

# 4) Create an OpenAI LLM wrapper (we’ll use gpt-3.5-turbo with temperature=0 for SQL generation)
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    model="gpt-3.5-turbo",
    temperature=0.0
)

# 5) Build a SQLDatabaseChain: it will prompt OpenAI to generate SQL, run it in DuckDB, and return results.
sql_chain = SQLDatabaseChain.from_llm(
    llm=ChatOpenAI(temperature=0),  # whatever params you want
    db=db,
    top_k=20,
    verbose=True,
    return_direct=True
)


def _parse_rows(result_str: str) -> list[tuple]:
    """Parse the SQL agent output string into ``list[tuple]`` rows."""
    try:
        return ast.literal_eval(result_str)
    except Exception:
        pass

    try:
        start = result_str.index("[")
        end = result_str.rindex("]") + 1
        snippet = result_str[start:end]
        return ast.literal_eval(snippet)
    except Exception as exc:
        raise ValueError(f"Unable to parse SQL result: {result_str}") from exc

def query_via_sqlagent(user_question: str) -> list[tuple]:
    """Return query results for ``user_question`` using the SQL agent.

    If the initial attempt fails, a second attempt is made with an
    appended ``LIMIT`` clause to reduce the data volume.  SQL statements
    are never returned to the caller.
    """

    try:
        result_str = sql_chain.run(user_question)
        return _parse_rows(result_str)

    except Exception:
        # Retry with a small LIMIT in case the generated query was invalid
        retry_q = f"{user_question.strip()} LIMIT 10"
        try:
            result_str = sql_chain.run(retry_q)
            return _parse_rows(result_str)
        except Exception as e:
            raise RuntimeError(f"SQLAgent error after retry: {e}") from e
