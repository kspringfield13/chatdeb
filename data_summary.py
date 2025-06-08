import base64
from io import BytesIO
import duckdb
import graphviz


def summarize_duckdb(db_path="data/data.db"):
    con = duckdb.connect(db_path)
    tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
    lines = []
    for t in tables:
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            count = "?"
        lines.append(f"{t}: {count} rows")
    return "\n".join(lines)


def erd_as_base64(db_path="data/data.db"):
    con = duckdb.connect(db_path)
    tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
    dot = graphviz.Digraph()
    for t in tables:
        cols = [row[1] for row in con.execute(f"PRAGMA table_info('{t}')").fetchall()]
        label = f"{{{t}|" + "\\l".join(cols) + "\\l}}"
        dot.node(t, label=label, shape="record", fontname="Helvetica", fontsize="10")
    # naive edges based on *_id columns
    for t in tables:
        cols = [row[1] for row in con.execute(f"PRAGMA table_info('{t}')").fetchall()]
        for c in cols:
            if c.endswith("_id"):
                for other in tables:
                    if other != t and c in [
                        r[1]
                        for r in con.execute(f"PRAGMA table_info('{other}')").fetchall()
                    ]:
                        dot.edge(t, other)
    png_data = dot.pipe(format="png")
    return base64.b64encode(png_data).decode("utf-8")
