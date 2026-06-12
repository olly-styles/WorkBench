from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
from results_data import load_model_results

TOTAL_TASKS = 690

VENDOR_COLORS = {
    "OpenAI": "#10a37f",
    "Anthropic": "#d97757",
    "Google": "#4285f4",
    "Open weights": "#8250df",
}

# All models run on WorkBench against their verified public release date.
MODELS = [
    {
        "label": "GPT-3.5-turbo",
        "vendor": "OpenAI",
        "release": date(2023, 3, 1),
        "dx": 8,
        "dy": -3,
        "ha": "left",
    },
    {
        "label": "GPT-4-turbo",
        "vendor": "OpenAI",
        "release": date(2023, 11, 6),
        "dx": 8,
        "dy": -13,
        "ha": "left",
    },
    {
        "label": "GPT-4o",
        "vendor": "OpenAI",
        "release": date(2024, 5, 13),
        "dx": 8,
        "dy": 5,
        "ha": "left",
    },
    {
        "label": "GPT-4.1",
        "vendor": "OpenAI",
        "release": date(2025, 4, 14),
        "dx": -8,
        "dy": -13,
        "ha": "right",
    },
    {"label": "o3", "vendor": "OpenAI", "release": date(2025, 4, 16), "dx": 4, "dy": 8, "ha": "left"},
    {
        "label": "GPT-5",
        "vendor": "OpenAI",
        "release": date(2025, 8, 7),
        "dx": -2,
        "dy": 9,
        "ha": "right",
    },
    {
        "label": "GLM-4.6",
        "vendor": "Open weights",
        "release": date(2025, 9, 30),
        "dx": 6,
        "dy": -13,
        "ha": "left",
    },
    {
        "label": "Haiku 4.5",
        "vendor": "Anthropic",
        "release": date(2025, 10, 15),
        "dx": 6,
        "dy": 6,
        "ha": "left",
    },
    {
        "label": "GPT-5.1",
        "vendor": "OpenAI",
        "release": date(2025, 11, 12),
        "dx": 0,
        "dy": -16,
        "ha": "center",
    },
    {
        "label": "GPT-5.2",
        "vendor": "OpenAI",
        "release": date(2025, 12, 11),
        "dx": -6,
        "dy": 8,
        "ha": "right",
    },
    {
        "label": "Sonnet 4.6",
        "vendor": "Anthropic",
        "release": date(2026, 2, 17),
        "dx": -6,
        "dy": 6,
        "ha": "right",
    },
    {
        "label": "Gemini-3.1-pro",
        "vendor": "Google",
        "release": date(2026, 2, 19),
        "dx": 0,
        "dy": 9,
        "ha": "center",
    },
    {
        "label": "Qwen3.5",
        "vendor": "Open weights",
        "release": date(2026, 2, 23),
        "dx": -6,
        "dy": -13,
        "ha": "right",
    },
    {
        "label": "GPT-5.4-nano",
        "vendor": "OpenAI",
        "release": date(2026, 3, 5),
        "dx": 5,
        "dy": -12,
        "ha": "left",
    },
    {
        "label": "GPT-5.4-mini",
        "vendor": "OpenAI",
        "release": date(2026, 3, 5),
        "dx": 5,
        "dy": -3,
        "ha": "left",
    },
    {
        "label": "GPT-5.4",
        "vendor": "OpenAI",
        "release": date(2026, 3, 5),
        "dx": -6,
        "dy": 6,
        "ha": "right",
    },
    {
        "label": "Mistral-Small-4",
        "vendor": "Open weights",
        "release": date(2026, 3, 16),
        "dx": 5,
        "dy": -12,
        "ha": "left",
    },
    {
        "label": "Kimi-K2.6",
        "vendor": "Open weights",
        "release": date(2026, 4, 20),
        "dx": -8,
        "dy": 1,
        "ha": "right",
    },
    {
        "label": "GPT-5.5",
        "vendor": "OpenAI",
        "release": date(2026, 4, 23),
        "dx": -5,
        "dy": -13,
        "ha": "right",
    },
    {
        "label": "DeepSeek-V4-pro",
        "vendor": "Open weights",
        "release": date(2026, 4, 24),
        "dx": 6,
        "dy": -3,
        "ha": "left",
    },
    {
        "label": "Mistral-Medium-3.5",
        "vendor": "Open weights",
        "release": date(2026, 4, 30),
        "dx": 6,
        "dy": -12,
        "ha": "left",
    },
    {
        "label": "Gemini-3.5-flash",
        "vendor": "Google",
        "release": date(2026, 5, 19),
        "dx": 5,
        "dy": -11,
        "ha": "left",
    },
    {
        "label": "Opus 4.8",
        "vendor": "Anthropic",
        "release": date(2026, 5, 28),
        "dx": 5,
        "dy": -10,
        "ha": "left",
    },
    {
        "label": "Fable 5",
        "vendor": "Anthropic",
        "release": date(2026, 6, 9),
        "dx": 5,
        "dy": 4,
        "ha": "left",
    },
]

RESULTS = load_model_results()
for model in MODELS:
    model["correct"] = RESULTS[model["label"]]["correct"]
    model["accuracy"] = 100 * model["correct"] / TOTAL_TASKS

print(f"{'Model':<18}{'Vendor':<14}{'Release':>12}{'Completion':>14}")
for model in sorted(MODELS, key=lambda m: m["release"]):
    print(f"{model['label']:<18}{model['vendor']:<14}{model['release'].isoformat():>12}{model['accuracy']:>12.1f}%")

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

fig, ax = plt.subplots(figsize=(7.4, 5.0))

frontier = []
running_max = -1.0
for model in sorted(MODELS, key=lambda m: m["release"]):
    if model["accuracy"] > running_max:
        frontier.append(model)
        running_max = model["accuracy"]
ax.plot(
    [m["release"] for m in frontier],
    [m["accuracy"] for m in frontier],
    color="#888888",
    linewidth=1.2,
    alpha=0.5,
    zorder=2,
)

frontier_labels = {m["label"] for m in frontier}
seen = set()
for model in MODELS:
    vendor = model["vendor"]
    ax.scatter(
        model["release"],
        model["accuracy"],
        s=130,
        color=VENDOR_COLORS[vendor],
        edgecolor="white",
        linewidth=1.2,
        zorder=3,
        label=vendor if vendor not in seen else None,
    )
    seen.add(vendor)
    if model["label"] in frontier_labels:
        ax.annotate(
            model["label"],
            xy=(model["release"], model["accuracy"]),
            xytext=(model["dx"], model["dy"]),
            textcoords="offset points",
            fontsize=8,
            color="#222222",
            ha=model["ha"],
            zorder=4,
        )

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator((1, 4, 7, 10)))
ax.set_ylim(0, 100)
ax.yaxis.set_major_locator(MultipleLocator(10))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))

ax.set_xlabel("Model release date")
ax.set_ylabel("Successful task completion (%)")
ax.set_title("Task completion on WorkBench by release date", pad=12)

ax.grid(True, which="major", color="#dddddd", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(frameon=False, loc="lower right", ncol=2, fontsize=10)

out_dir = Path(__file__).parent
fig.savefig(out_dir / "completion_vs_release_all.pdf")
fig.savefig(out_dir / "completion_vs_release_all.png", dpi=220)
print("wrote completion_vs_release_all.pdf and .png")
