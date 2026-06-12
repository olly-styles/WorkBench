from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
from results_data import load_model_results

TOTAL_TASKS = 690

# OpenAI models on WorkBench, ordered by release date. "release" is the public
# release date (verified against published announcements). Correct counts come
# from the generated results artifact (retro/data/model_results.json).
MODELS = [
    {"label": "GPT-3.5-turbo", "release": date(2023, 3, 1), "dx": 8, "dy": -4, "ha": "left"},
    {"label": "GPT-4-turbo", "release": date(2023, 11, 6), "dx": 8, "dy": -14, "ha": "left"},
    {"label": "GPT-4o", "release": date(2024, 5, 13), "dx": 8, "dy": 4, "ha": "left"},
    {"label": "GPT-4.1", "release": date(2025, 4, 14), "dx": -8, "dy": -14, "ha": "right"},
    {"label": "o3", "release": date(2025, 4, 16), "dx": 4, "dy": 9, "ha": "left"},
    {"label": "GPT-5", "release": date(2025, 8, 7), "dx": 0, "dy": 12, "ha": "center"},
    {"label": "GPT-5.1", "release": date(2025, 11, 12), "dx": 0, "dy": -17, "ha": "center"},
    {"label": "GPT-5.2", "release": date(2025, 12, 11), "dx": -9, "dy": 6, "ha": "right"},
    {"label": "GPT-5.4-nano", "release": date(2026, 3, 5), "dx": 9, "dy": -10, "ha": "left"},
    {"label": "GPT-5.4-mini", "release": date(2026, 3, 5), "dx": 9, "dy": 0, "ha": "left"},
    {"label": "GPT-5.4", "release": date(2026, 3, 5), "dx": -9, "dy": 8, "ha": "right"},
    {"label": "GPT-5.5", "release": date(2026, 4, 23), "dx": 8, "dy": 4, "ha": "left"},
]

POINT_COLOR = "#1b6ca8"

RESULTS = load_model_results()
models = MODELS
for model in models:
    model["correct"] = RESULTS[model["label"]]["correct"]
    model["accuracy"] = 100 * model["correct"] / TOTAL_TASKS

print(f"{'Model':<16}{'Release':>14}{'Completion':>16}")
for model in models:
    completion = f"{model['correct']}/{TOTAL_TASKS} ({model['accuracy']:.1f}%)"
    print(f"{model['label']:<16}{model['release'].isoformat():>14}{completion:>16}")

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.labelsize": 13,
        "mathtext.fontset": "cm",
        "axes.linewidth": 0.9,
        "savefig.bbox": "tight",
    }
)

fig, ax = plt.subplots(figsize=(6.6, 4.6))

frontier = []
running_max = -1.0
for model in sorted(models, key=lambda m: m["release"]):
    if model["accuracy"] > running_max:
        frontier.append(model)
        running_max = model["accuracy"]
ax.plot(
    [m["release"] for m in frontier],
    [m["accuracy"] for m in frontier],
    color=POINT_COLOR,
    linewidth=1.1,
    alpha=0.35,
    zorder=2,
)

frontier_labels = {m["label"] for m in frontier}
for model in models:
    ax.scatter(
        model["release"],
        model["accuracy"],
        s=150,
        color=POINT_COLOR,
        edgecolor="white",
        linewidth=1.3,
        zorder=3,
    )
    if model["label"] in frontier_labels:
        ax.annotate(
            model["label"],
            xy=(model["release"], model["accuracy"]),
            xytext=(model["dx"], model["dy"]),
            textcoords="offset points",
            fontsize=10,
            color="#222222",
            ha=model["ha"],
            zorder=4,
        )

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_ylim(0, 100)
ax.yaxis.set_major_locator(MultipleLocator(20))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))

ax.set_xlabel("Model release date")
ax.set_ylabel("Successful task completion (%)")
ax.set_title("OpenAI task completion on WorkBench over time", pad=12)

ax.grid(True, which="major", color="#dddddd", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

out_dir = Path(__file__).parent
fig.savefig(out_dir / "completion_vs_release.pdf")
fig.savefig(out_dir / "completion_vs_release.png", dpi=220)
print("wrote completion_vs_release.pdf and .png")
