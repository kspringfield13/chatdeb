from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env located in the package root
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')

def is_testing() -> bool:
    return os.getenv('KYDXBOT_TESTING') == '1'

TESTING = is_testing()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME')

CHARTS_DIR = ROOT / 'charts'
CHARTS_DIR.mkdir(exist_ok=True)

# Directory for temporary database when ingesting user files
INGEST_DIR = ROOT / 'ingested_data'
INGEST_DIR.mkdir(exist_ok=True)

# DuckDB path used for ingested user data
INGEST_DB_PATH = INGEST_DIR / 'ingest.db'


def require_env(*names: str) -> None:
    """Raise ``ValueError`` if any of ``names`` are unset and not testing."""
    if is_testing():
        return
    missing = [n for n in names if not os.getenv(n)]
    if missing:
        raise ValueError('Missing environment variables: ' + ', '.join(missing))
