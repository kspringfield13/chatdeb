import matplotlib.pyplot as plt


def set_default_style() -> None:
    """Apply a consistent dark style for all generated charts."""
    plt.style.use("dark_background")
    plt.rcParams.update(
        {
            "figure.facecolor": "#1f1f1f",
            "axes.facecolor": "#1f1f1f",
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#DDDDDD",
            "axes.labelcolor": "#DDDDDD",
            "text.color": "#DDDDDD",
            "xtick.color": "#DDDDDD",
            "ytick.color": "#DDDDDD",
            "axes.grid": True,
            "grid.color": "#444444",
            "grid.linestyle": "--",
            "grid.linewidth": 0.5,
        }
    )
