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

def query_via_sqlagent(user_question: str) -> list[tuple]:
    """
    1) Call sql_chain.run(...) to get back a single string that looks like:
         "[(8794, 'Sarah', 'Brown', 251.37), …]"
    2) literal_eval that string into a real list of tuples.
    3) Return that list of tuples. No column names.
    """
    try:
        result_str = sql_chain.run(user_question)
        # result_str is something like: "[(8794, 'Sarah','Brown',251.37), …]"
        rows = ast.literal_eval(result_str)
        # rows is now a Python list[tuple].  
        return rows

    except Exception as e:
        # If anything goes wrong, bubble up an exception
        raise RuntimeError(f"SQLAgent error: {e}")