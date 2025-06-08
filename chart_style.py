import matplotlib.pyplot as plt


def set_default_style() -> None:
    """Apply a consistent style for all generated charts."""
    plt.style.use("seaborn-v0_8-darkgrid")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#333333",
            "axes.grid": True,
            "grid.color": "#e0e0e0",
            "grid.linestyle": "--",
            "grid.linewidth": 0.5,
        }
    )
