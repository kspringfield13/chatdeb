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
    """Create a visually appealing ER diagram from table relationships."""
    con = duckdb.connect(db_path)
    tables = sorted(row[0] for row in con.execute("SHOW TABLES").fetchall())
    edges = []
    for tbl in tables:
        cols = [row[0] for row in con.execute(f"DESCRIBE {tbl}").fetchall()]
        cols = sorted(cols)
        for col in cols:
            if col.endswith("_id"):
                ref = col[:-3]
                for t in tables:
                    if t == ref or t.rstrip("s") == ref:
                        edges.append((tbl, t))
                        break
    con.close()

    G = nx.DiGraph()
    for t in tables:
        G.add_node(t)
    for a, b in edges:
        G.add_edge(a, b)

    pos = nx.spring_layout(G, k=1)

    plt.figure(figsize=(10, 7), facecolor="#1f1f1f")
    ax = plt.gca()
    ax.set_facecolor("#1f1f1f")
    ax.set_axis_off()  # remove grid, ticks, and axis

    labels = {t: t[:20] for t in G.nodes()}

    nx.draw_networkx_nodes(
        G,
        pos,
        node_color="#2b2b2b",
        edgecolors="#ffffff",
        node_size=1800,
        linewidths=1.5,
        alpha=0.9,
    )

    nx.draw_networkx_edges(
        G,
        pos,
        edge_color="#888888",
        arrows=True,
        arrowstyle="->",
        arrowsize=15,
        width=1.2,
    )

    nx.draw_networkx_labels(
        G,
        pos,
        labels=labels,
        font_size=10,
        font_color="#ffffff",
        font_family="sans-serif",
        font_weight="bold",
    )

    plt.title("Entity Relationship Diagram", fontsize=12, color="white", pad=20)
    OUTPUT_DIR.mkdir(exist_ok=True)
    outfile = OUTPUT_DIR / f"erd_{uuid.uuid4().hex}.png"
    plt.tight_layout(pad=3)
    plt.savefig(outfile, facecolor="#1f1f1f", dpi=300)
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
