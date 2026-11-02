"""Draw the brand icons in custom_components/.../brand/.

A noisy input signal behind its smoothed curve, on a rounded square with a
transparent background. Run with matplotlib available, for example:

    uv run --no-project --with matplotlib python scripts/plot_brand_icon.py
"""

import math
import random
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "custom_components/smoothing_analytics_sensors/brand"

BACKGROUND = "#03a9f4"
NOISE_POINTS = 46
SMOOTH_POINTS = 400


def curve(x: float) -> float:
    """Smooth signal in the unit square."""
    return 0.5 + 0.18 * math.sin(2 * math.pi * (x * 0.95 + 0.1))


def draw(size: int, path: Path) -> None:
    """Write one square icon of size x size pixels."""
    rng = random.Random(7)
    noise_x = [i / (NOISE_POINTS - 1) for i in range(NOISE_POINTS)]
    noise_y = [min(0.88, max(0.12, curve(x) + rng.gauss(0, 0.12))) for x in noise_x]
    smooth_x = [i / (SMOOTH_POINTS - 1) for i in range(SMOOTH_POINTS)]

    fig = plt.figure(figsize=(1, 1), dpi=size)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(
        FancyBboxPatch(
            (0, 0),
            1,
            1,
            boxstyle="round,pad=0,rounding_size=0.22",
            fc=BACKGROUND,
            ec="none",
        )
    )
    ax.plot(
        [0.12 + 0.76 * x for x in noise_x],
        noise_y,
        color="white",
        alpha=0.7,
        lw=2.4,
        solid_joinstyle="round",
        solid_capstyle="round",
    )
    ax.plot(
        [0.12 + 0.76 * x for x in smooth_x],
        [curve(x) for x in smooth_x],
        color="white",
        lw=5.5,
        solid_capstyle="round",
    )
    fig.savefig(path, transparent=True, dpi=size)
    plt.close(fig)


def main() -> None:
    """Write icon.png and icon@2x.png."""
    BRAND.mkdir(exist_ok=True)
    draw(256, BRAND / "icon.png")
    draw(512, BRAND / "icon@2x.png")


if __name__ == "__main__":
    main()
