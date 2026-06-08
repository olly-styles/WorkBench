from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

TOTAL_TASKS = 690

OPEN_WEIGHT_FAMILIES = {"Qwen", "DeepSeek", "Kimi", "GLM"}
LICENSE_COLORS = {"Proprietary": "#1b6ca8", "Open weights": "#c1440e"}

MODELS = [
    {
        "label": "Opus 4.8",
        "family": "Claude",
        "total_cost": 125.55,
        "correct": 613,
        "side_effects": 17,
        "dx": 9,
        "dy": 4,
        "ha": "left",
    },
    {
        "label": "GPT-5.5",
        "family": "GPT",
        "total_cost": 142.44,
        "correct": 605,
        "side_effects": 27,
        "dx": 9,
        "dy": -15,
        "ha": "left",
    },
    {
        "label": "Sonnet 4.6",
        "family": "Claude",
        "total_cost": 72.17,
        "correct": 557,
        "side_effects": 67,
        "dx": 9,
        "dy": -13,
        "ha": "left",
    },
    {
        "label": "Haiku 4.5",
        "family": "Claude",
        "total_cost": 23.47,
        "correct": 466,
        "side_effects": 115,
        "dx": 9,
        "dy": 6,
        "ha": "left",
    },
    {
        "label": "GPT-5.4-mini",
        "family": "GPT",
        "total_cost": 18.95,
        "correct": 372,
        "side_effects": 209,
        "dx": 9,
        "dy": -15,
        "ha": "left",
    },
    {
        "label": "GPT-5.4-nano",
        "family": "GPT",
        "total_cost": 4.84,
        "correct": 305,
        "side_effects": 197,
        "dx": 9,
        "dy": 6,
        "ha": "left",
    },
    {
        "label": "Qwen3.5",
        "family": "Qwen",
        "total_cost": 1.82,
        "correct": 436,
        "side_effects": 148,
        "dx": 9,
        "dy": 7,
        "ha": "left",
    },
    {
        "label": "GPT-4-turbo",
        "family": "GPT",
        "total_cost": 211.89,
        "correct": 391,
        "side_effects": 154,
        "dx": -9,
        "dy": 4,
        "ha": "right",
    },
    {
        "label": "DeepSeek-V4-pro",
        "family": "DeepSeek",
        "total_cost": 11.48,
        "correct": 537,
        "side_effects": 88,
        "dx": -9,
        "dy": 0,
        "ha": "right",
    },
    {
        "label": "Gemini-3.5-flash",
        "family": "Gemini",
        "total_cost": 46.23,
        "correct": 581,
        "side_effects": 21,
        "dx": 9,
        "dy": -6,
        "ha": "left",
    },
    {
        "label": "Gemini-3.1-pro",
        "family": "Gemini",
        "total_cost": 52.68,
        "correct": 605,
        "side_effects": 21,
        "dx": 0,
        "dy": 11,
        "ha": "center",
    },
    {
        "label": "Kimi-K2.6",
        "family": "Kimi",
        "total_cost": 15.51,
        "correct": 556,
        "side_effects": 47,
        "dx": -9,
        "dy": 6,
        "ha": "right",
    },
    {
        "label": "GLM-4.6",
        "family": "GLM",
        "total_cost": 11.49,
        "correct": 488,
        "side_effects": 118,
        "dx": -9,
        "dy": -4,
        "ha": "right",
    },
    {
        "label": "GPT-4o",
        "family": "GPT",
        "total_cost": 46.67,
        "correct": 434,
        "side_effects": 104,
        "dx": 9,
        "dy": -3,
        "ha": "left",
    },
    {
        "label": "GPT-3.5-turbo",
        "family": "GPT",
        "total_cost": 10.78,
        "correct": 178,
        "side_effects": 267,
        "dx": 9,
        "dy": 6,
        "ha": "left",
    },
    {
        "label": "o3",
        "family": "GPT",
        "total_cost": 49.50,
        "correct": 490,
        "side_effects": 121,
        "dx": 8,
        "dy": 8,
        "ha": "left",
    },
    {
        "label": "GPT-4.1",
        "family": "GPT",
        "total_cost": 45.06,
        "correct": 483,
        "side_effects": 134,
        "dx": 0,
        "dy": -15,
        "ha": "center",
    },
    {
        "label": "GPT-5",
        "family": "GPT",
        "total_cost": 34.32,
        "correct": 536,
        "side_effects": 90,
        "dx": 0,
        "dy": 10,
        "ha": "center",
    },
    {
        "label": "GPT-5.1",
        "family": "GPT",
        "total_cost": 24.55,
        "correct": 362,
        "side_effects": 125,
        "dx": -9,
        "dy": -12,
        "ha": "right",
    },
    {
        "label": "GPT-5.2",
        "family": "GPT",
        "total_cost": 38.21,
        "correct": 437,
        "side_effects": 130,
        "dx": 9,
        "dy": -13,
        "ha": "left",
    },
    {
        "label": "GPT-5.4",
        "family": "GPT",
        "total_cost": 59.91,
        "correct": 491,
        "side_effects": 116,
        "dx": -9,
        "dy": 9,
        "ha": "right",
    },
]

for model in MODELS:
    model["accuracy"] = 100 * model["correct"] / TOTAL_TASKS
    model["side_effect_rate"] = 100 * model["side_effects"] / TOTAL_TASKS
    model["cost_per_task"] = model["total_cost"] / TOTAL_TASKS

# Efficient frontier: cheapest model for each completion level (no other model is
# both cheaper and more capable). Sort by cost, tie-break to the higher accuracy.
FRONTIER = []
_best = -1.0
for model in sorted(MODELS, key=lambda m: (m["cost_per_task"], -m["accuracy"])):
    if model["accuracy"] > _best:
        FRONTIER.append(model)
        _best = model["accuracy"]
FRONTIER_LABELS = {m["label"] for m in FRONTIER}
# Off-frontier models to label anyway: oldest, weakest, and cheapest tier.
LABEL_EXTRAS = {"GPT-4-turbo", "GPT-3.5-turbo", "GPT-5.4-nano"}

print(f"{'Model':<16}{'Completion':>16}{'Side effects':>18}{'Cost':>10}{'Cost/task':>12}")
for model in MODELS:
    completion = f"{model['correct']}/{TOTAL_TASKS} ({model['accuracy']:.1f}%)"
    side = f"{model['side_effects']}/{TOTAL_TASKS} ({model['side_effect_rate']:.1f}%)"
    print(
        f"{model['label']:<16}{completion:>16}{side:>18}{'$' + format(model['total_cost'], '.2f'):>10}{'$' + format(model['cost_per_task'], '.4f'):>12}"
    )

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

ax.plot(
    [m["cost_per_task"] for m in FRONTIER],
    [m["accuracy"] for m in FRONTIER],
    color="#999999",
    linewidth=1.1,
    alpha=0.45,
    zorder=1,
)

seen_licenses = set()
for model in MODELS:
    license_type = "Open weights" if model["family"] in OPEN_WEIGHT_FAMILIES else "Proprietary"
    legend_label = license_type if license_type not in seen_licenses else None
    seen_licenses.add(license_type)
    ax.scatter(
        model["cost_per_task"],
        model["accuracy"],
        s=110,
        color=LICENSE_COLORS[license_type],
        edgecolor="white",
        linewidth=1.3,
        zorder=3,
        label=legend_label,
    )
    if model["label"] in FRONTIER_LABELS or model["label"] in LABEL_EXTRAS:
        ax.annotate(
            model["label"],
            xy=(model["cost_per_task"], model["accuracy"]),
            xytext=(model["dx"], model["dy"]),
            textcoords="offset points",
            fontsize=8,
            color="#222222",
            ha=model["ha"],
            zorder=4,
        )

ax.set_xscale("log")
ax.set_xlim(0.0018, 0.45)
ax.set_ylim(0, 100)
ax.set_xticks([0.001, 0.01, 0.1])


def money(value: float, _: object) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return f"${text}"


ax.xaxis.set_major_formatter(FuncFormatter(money))
ax.yaxis.set_major_locator(MultipleLocator(10))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))

ax.set_xlabel("Cost per task (USD, log scale)")
ax.set_ylabel("Successful task completion (%)")
ax.set_title("Cost per task vs. task completion on WorkBench", pad=12)

ax.grid(True, which="major", color="#dddddd", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(frameon=False, loc="upper left")

out_dir = Path(__file__).parent
fig.savefig(out_dir / "cost_vs_accuracy.pdf")
fig.savefig(out_dir / "cost_vs_accuracy.png", dpi=220)
print("wrote cost_vs_accuracy.pdf and .png")
