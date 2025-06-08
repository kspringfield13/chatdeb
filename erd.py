import uuid
import base64
from pathlib import Path
import duckdb
import networkx as nx
import matplotlib.pyplot as plt
try:  # OpenAI is optional for ERD descriptions
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dep may be missing
    OpenAI = None

from .chart_style import set_default_style
from .db import DUCKDB_PATH

set_default_style()
# Save ER diagrams in the same ``charts`` folder used by other modules so the
# FastAPI server can serve them under the ``/charts`` route.
OUTPUT_DIR = Path("charts")

def get_data_summary(db_path: str = DUCKDB_PATH) -> str:
    """Return a human readable summary of the tables in the DuckDB database."""
    con = duckdb.connect(db_path)
    tables = sorted(row[0] for row in con.execute("SHOW TABLES").fetchall())

    details = []
    for tbl in tables:
        cols = [row[0] for row in con.execute(f"DESCRIBE {tbl}").fetchall()]
        cols = sorted(cols)
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        except Exception:
            count = "?"
        sample_cols = ", ".join(cols[:5])
        details.append(
            f"The '{tbl}' table contains {count} rows and columns such as {sample_cols}."
        )

    con.close()

    if not tables:
        return "The database is empty." 

    intro = f"The database contains {len(tables)} tables: {', '.join(tables)}."
    return " ".join([intro] + details)


def generate_erd(db_path: str = DUCKDB_PATH) -> str:
    """Create a basic ER diagram from table relationships."""
    con = duckdb.connect(db_path)
    tables = sorted(row[0] for row in con.execute("SHOW TABLES").fetchall())
    edges = []
    for tbl in tables:
        cols = [row[0] for row in con.execute(f"DESCRIBE {tbl}").fetchall()]
        cols = sorted(cols)
        for col in cols:
            if col.endswith("_id"):
                ref = col[:-3]
                # naive match to other table
                for t in tables:
                    if t == ref or t.rstrip('s') == ref:
                        edges.append((tbl, t))
                        break
    con.close()

    G = nx.DiGraph()
    for t in tables:
        G.add_node(t)
    for a, b in edges:
        G.add_edge(a, b)

    pos = nx.spring_layout(G, k=1)
    plt.figure(figsize=(8, 6), facecolor="#1f1f1f")
    ax = plt.gca()
    ax.set_facecolor("#1f1f1f")
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color="#333333",
        edgecolors="white",
        node_size=1500,
        font_size=8,
        font_color="white",
        font_weight="bold",
        edge_color="white",
    )
    OUTPUT_DIR.mkdir(exist_ok=True)
    outfile = OUTPUT_DIR / f"erd_{uuid.uuid4().hex}.png"
    plt.tight_layout()
    plt.savefig(outfile, facecolor="#1f1f1f")
    plt.close()
    return str(outfile)


def describe_erd(image_path: str) -> str:
    """Return a short text description of the ER diagram using OpenAI Vision.

    If the OpenAI dependency or API credentials are missing, an empty string is
    returned instead of raising an error.
    """
    if OpenAI is None:
        return ""
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        image_url = f"data:image/png;base64,{b64}"

        client = OpenAI()
        msg = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Describe the key tables and relationships shown in this ER diagram."
                    ),
                },
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[msg],
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:  # noqa: BLE001
        print("vision ERD error", exc)
        return ""
