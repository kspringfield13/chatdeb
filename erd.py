import uuid
from pathlib import Path
import duckdb
import networkx as nx
import matplotlib.pyplot as plt
from .chart_style import set_default_style
from .db import DUCKDB_PATH

set_default_style()
OUTPUT_DIR = Path(__file__).resolve().parent / "charts"
OUTPUT_DIR.mkdir(exist_ok=True)

def get_data_summary(db_path: str = DUCKDB_PATH) -> str:
    """Return a short textual summary of tables in the DuckDB database."""
    con = duckdb.connect(db_path)
    tables = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
    lines = []
    for tbl in tables:
        cols = [row[0] for row in con.execute(f"DESCRIBE {tbl}").fetchall()]
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        except Exception:
            count = "?"
        lines.append(f"{tbl}: {count} rows, cols: {', '.join(cols[:5])}")
    con.close()
    return "\n".join(lines)


def generate_erd(db_path: str = DUCKDB_PATH) -> str:
    """Create a basic ER diagram from table relationships."""
    con = duckdb.connect(db_path)
    tables = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
    edges = []
    for tbl in tables:
        cols = [row[0] for row in con.execute(f"DESCRIBE {tbl}").fetchall()]
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
    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_color="#00FFE1", edgecolors="black", node_size=1500, font_size=8)
    outfile = OUTPUT_DIR / f"erd_{uuid.uuid4().hex}.png"
    plt.tight_layout()
    plt.savefig(outfile)
    plt.close()
    return str(outfile)
