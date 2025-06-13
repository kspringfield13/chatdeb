import os
import json
import base64
import io
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI

RAW_DIR = Path(__file__).resolve().parent / "../raw_data"
# Store extracted metadata alongside the ingested database so that the chatbot
# always references the latest ingested dataset.
OUT_FILE = Path(__file__).resolve().parent / "../ingested_data/metadata.json"


def _capture_preview_image(df: pd.DataFrame) -> str:
    """Return a base64 PNG of the dataframe head."""
    text = df.head().to_markdown(index=False)
    fig, ax = plt.subplots(figsize=(6, 0.5 + 0.25 * len(df.head())))
    ax.axis("off")
    ax.text(0.01, 0.99, text, fontsize=8, family="monospace", va="top")
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def analyze_file(path: Path) -> dict:
    """Analyze a data file using OpenAI Vision and return metadata."""
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xls", ".xlsx"}:
        engine = "openpyxl" if path.suffix.lower() == ".xlsx" else "xlrd"
        df = pd.read_excel(path, engine=engine)
    elif path.suffix.lower() == ".json":
        df = pd.read_json(path, orient="records", lines=False)
    else:
        return {}

    image_url = _capture_preview_image(df)

    client = OpenAI()
    message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    "Examine this dataset preview. "
                    "Identify any titles or headers and provide a short summary "
                    "of what information the data contains."
                ),
            },
            {"type": "image_url", "image_url": {"url": image_url}},
        ],
    }
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[message],
        )
        summary = resp.choices[0].message.content.strip()
    except Exception as exc:  # noqa: BLE001
        print("vision metadata error", exc)
        summary = ""

    return {"headers": df.columns.tolist(), "summary": summary}


def generate_metadata(raw_dir: Path = RAW_DIR, out_file: Path = OUT_FILE) -> None:
    metadata = {}
    for file in os.listdir(raw_dir):
        path = Path(raw_dir) / file
        if not path.is_file():
            continue
        info = analyze_file(path)
        if info:
            metadata[file] = info
    try:
        out_file.parent.mkdir(exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    except Exception as exc:  # noqa: BLE001
        print("vision metadata write error", exc)


if __name__ == "__main__":
    generate_metadata()
