import os
import random
import uuid
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from PIL import Image
from .chart_style import set_default_style
from .erd import WATERMARK_PATH

set_default_style()
import numpy as np

OUTPUT_DIR = Path("charts")
OUTPUT_DIR.mkdir(exist_ok=True)


def bar_chart(ax, data, labels, title="Bar Chart"):
    ax.bar(labels, data, color="skyblue")
    ax.set_title(title, fontsize=10, color="white")
    # Set ticks explicitly before applying labels to avoid matplotlib warnings
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, fontsize=8)


def line_chart(ax, data, labels, title="Line Chart"):
    ax.plot(labels, data, marker="o", color="coral")
    ax.set_title(title, fontsize=10, color="white")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, fontsize=8)


def pie_chart(ax, data, labels, title="Pie Chart"):
    ax.pie(data, labels=labels, autopct="%1.1f%%", textprops={"fontsize": 8})
    ax.set_title(title, fontsize=10, color="white")


def scatter_chart(ax, x, y, title="Scatter Chart"):
    ax.scatter(x, y, color="seagreen")
    ax.set_title(title, fontsize=10, color="white")
    ax.set_xlabel("X", fontsize=8)
    ax.set_ylabel("Y", fontsize=8)


def histogram_chart(ax, data, bins=5, title="Histogram"):
    ax.hist(data, bins=bins, color="orchid")
    ax.set_title(title, fontsize=10, color="white")


def render_table(ax, table_data, col_labels, title="Data Table"):
    ax.axis("off")
    ax.set_title(title, fontsize=10, color="white")
    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#777777")
        cell.set_linewidth(0.5)
        if row == 0:
            cell.set_facecolor("#333333")
            cell.set_text_props(weight="bold", color="white")
        else:
            cell.set_facecolor("#1f1f1f")
            cell.set_text_props(color="#e0e0e0")


def layout1(content, outfile):
    """Generate infographic layout 1 and save to ``outfile``."""
    fig = plt.figure(figsize=(8, 10), facecolor="#1f1f1f")
    gs = GridSpec(4, 2, figure=fig, height_ratios=[0.5, 2, 2, 2])

    fig.suptitle(content["title"], fontsize=16, y=0.95, color="white")
    fig.text(0.5, 0.90, content["big_number"], ha="center", fontsize=14, color="white")

    ax1 = fig.add_subplot(gs[1, 0])
    bar_chart(ax1, *content["charts"][0])

    ax2 = fig.add_subplot(gs[1, 1])
    line_chart(ax2, *content["charts"][1])

    ax3 = fig.add_subplot(gs[2, 0])
    pie_chart(ax3, *content["charts"][2])

    ax4 = fig.add_subplot(gs[2, 1])
    scatter_chart(ax4, *content["charts"][3])

    ax5 = fig.add_subplot(gs[3, 0])
    histogram_chart(
        ax5,
        content["charts"][4][0],
        bins=content["charts"][4][1],
        title=content["charts"][4][2],
    )

    ax_table = fig.add_subplot(gs[3, 1])
    render_table(
        ax_table, content["table_data"], content["table_cols"], title="Summary Table"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.89])
    fig.savefig(outfile, dpi=300, facecolor="#1f1f1f")
    plt.close(fig)


def layout2(content, outfile):
    """Generate infographic layout 2 and save to ``outfile``."""
    fig = plt.figure(figsize=(8, 10), facecolor="#1f1f1f")
    gs = GridSpec(4, 2, figure=fig, height_ratios=[3, 2, 1, 2])

    fig.suptitle(content["title"], fontsize=16, y=0.98, color="white")

    ax1 = fig.add_subplot(gs[0, :])
    bar_chart(ax1, *content["charts"][0])

    ax2 = fig.add_subplot(gs[1, 0])
    line_chart(ax2, *content["charts"][1])

    ax3 = fig.add_subplot(gs[1, 1])
    pie_chart(ax3, *content["charts"][2])

    ax_big = fig.add_subplot(gs[2, 0])
    ax_big.axis("off")
    ax_big.text(
        0.5,
        0.5,
        content["big_number"],
        ha="center",
        va="center",
        fontsize=14,
        color="white",
    )
    ax_big.set_title("Key Metric", fontsize=10, color="white")

    ax_table = fig.add_subplot(gs[2, 1])
    render_table(
        ax_table, content["table_data"], content["table_cols"], title="Summary Table"
    )

    ax4 = fig.add_subplot(gs[3, :])
    scatter_chart(ax4, *content["charts"][3][:2], title=content["charts"][3][2])

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(outfile, dpi=300, facecolor="#1f1f1f")
    plt.close(fig)


def layout3(content, outfile):
    """Generate infographic layout 3 and save to ``outfile``."""
    fig = plt.figure(figsize=(8, 10), facecolor="#1f1f1f")
    gs = GridSpec(3, 3, figure=fig, height_ratios=[0.8, 2, 2])

    ax_title = fig.add_subplot(gs[0, 0:2])
    ax_title.axis("off")
    ax_title.text(
        0,
        0.5,
        content["title"],
        ha="left",
        va="center",
        fontsize=16,
        color="white",
    )

    ax_big = fig.add_subplot(gs[0, 2])
    ax_big.axis("off")
    ax_big.text(
        0.5,
        0.5,
        content["big_number"],
        ha="center",
        va="center",
        fontsize=14,
        color="white",
    )
    ax_big.set_title("Key Metric", fontsize=10, color="white")

    ax1 = fig.add_subplot(gs[1, 0])
    pie_chart(ax1, *content["charts"][2])

    ax2 = fig.add_subplot(gs[1, 1])
    scatter_chart(ax2, *content["charts"][3][:2], title=content["charts"][3][2])

    ax3 = fig.add_subplot(gs[1, 2])
    histogram_chart(
        ax3,
        content["charts"][4][0],
        bins=content["charts"][4][1],
        title=content["charts"][4][2],
    )

    ax4 = fig.add_subplot(gs[2, 0])
    bar_chart(ax4, *content["charts"][0])

    ax5 = fig.add_subplot(gs[2, 1])
    line_chart(ax5, *content["charts"][1])

    ax_table = fig.add_subplot(gs[2, 2])
    render_table(
        ax_table, content["table_data"], content["table_cols"], title="Summary Table"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(outfile, dpi=300, facecolor="#1f1f1f")
    plt.close(fig)


def generate_sample_content():
    """Return sample content for an infographic."""
    content = {
        "title": "Quarterly Performance Overview",
        "big_number": "$1.2M",
        "charts": [
            ([150, 200, 250, 300], ["Q1", "Q2", "Q3", "Q4"], "Revenue by Quarter"),
            ([50, 75, 60, 90], ["Q1", "Q2", "Q3", "Q4"], "Customer Growth"),
            (
                [40, 35, 25],
                ["Product A", "Product B", "Product C"],
                "Product Sales Share",
            ),
            ([1, 2, 3, 4, 5], [10, 15, 13, 20, 18], "Churn vs Lifetime Value"),
            (np.random.normal(50, 15, 100).tolist(), 7, "Distribution of Order Sizes"),
        ],
        "table_data": [
            ["Metric", "Value"],
            ["Total Orders", "3,500"],
            ["Active Customers", "1,200"],
            ["New Signups", "300"],
            ["Churn Rate", "5%"],
        ],
        "table_cols": ["Metric", "Value"],
    }
    return content


TEMPLATES = [layout1, layout2, layout3]


def create_infographic(answers: list[str]) -> str:
    """Create an infographic PNG and return its path.

    If a third answer is provided and points to an existing image file, that
    image will be embedded as the main chart in the infographic.
    """

    content = generate_sample_content()
    if answers:
        if len(answers) > 0 and answers[0].strip():
            content["title"] = answers[0].strip()
        if len(answers) > 1 and answers[1].strip():
            content["big_number"] = answers[1].strip()

    outfile = OUTPUT_DIR / f"infograph_{uuid.uuid4().hex}.png"

    img_path = answers[2] if len(answers) > 2 else None
    if img_path and os.path.exists(img_path):
        fig, ax = plt.subplots(figsize=(8, 10))
        ax.axis("off")
        ax.imshow(plt.imread(img_path))
        fig.suptitle(content["title"], fontsize=16, color="white")
        fig.savefig(outfile, dpi=300, bbox_inches="tight", facecolor="#1f1f1f")
        plt.close(fig)
    else:
        random.choice(TEMPLATES)(content, outfile)

    # Add optional watermark in bottom-right corner
    if WATERMARK_PATH.exists():
        try:
            base = Image.open(outfile).convert("RGBA")
            mark = Image.open(WATERMARK_PATH).convert("RGBA")
            max_width = int(base.width * 0.1)
            ratio = max_width / mark.width
            mark = mark.resize((max_width, int(mark.height * ratio)), Image.LANCZOS)
            x = base.width - mark.width - 10
            y = base.height - mark.height - 10
            base.alpha_composite(mark, dest=(x, y))
            base.save(outfile)
        except Exception:  # noqa: BLE001
            pass

    return str(outfile)


INTRO = "To create your infographic I'll need a bit more information."


def generate_infograph_questions(history: list[dict] | None = None) -> list[str]:
    """Return simple follow-up questions for building an infographic."""
    return [
        f"{INTRO} What should the title be?",
        "What key metric should be highlighted?",
    ]
