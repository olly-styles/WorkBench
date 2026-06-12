from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
from results_data import load_model_results

TOTAL_TASKS = 690

VENDOR_COLORS = {
    "OpenAI": "#10a37f",
    "Anthropic": "#d97757",
    "Google": "#4285f4",
    "Open weights": "#8250df",
}
CORRECT_COLOR = "#2a9d5a"
HARMLESS_COLOR = "#c9c9c9"
HARM_COLOR = "#c1440e"

# label, vendor, release. Correct/side-effect counts come from the generated
# results artifact (retro/data/model_results.json).
MODELS = [
    {"label": "GPT-3.5-turbo", "vendor": "OpenAI", "release": date(2023, 3, 1)},
    {"label": "GPT-4-turbo", "vendor": "OpenAI", "release": date(2023, 11, 6)},
    {"label": "GPT-4o", "vendor": "OpenAI", "release": date(2024, 5, 13)},
    {"label": "GPT-4.1", "vendor": "OpenAI", "release": date(2025, 4, 14)},
    {"label": "o3", "vendor": "OpenAI", "release": date(2025, 4, 16)},
    {"label": "GPT-5", "vendor": "OpenAI", "release": date(2025, 8, 7)},
    {"label": "GLM-4.6", "vendor": "Open weights", "release": date(2025, 9, 30)},
    {"label": "Haiku 4.5", "vendor": "Anthropic", "release": date(2025, 10, 15)},
    {"label": "GPT-5.1", "vendor": "OpenAI", "release": date(2025, 11, 12)},
    {"label": "GPT-5.2", "vendor": "OpenAI", "release": date(2025, 12, 11)},
    {"label": "Sonnet 4.6", "vendor": "Anthropic", "release": date(2026, 2, 17)},
    {"label": "Gemini-3.1-pro", "vendor": "Google", "release": date(2026, 2, 19)},
    {"label": "Qwen3.5", "vendor": "Open weights", "release": date(2026, 2, 23)},
    {"label": "GPT-5.4-nano", "vendor": "OpenAI", "release": date(2026, 3, 5)},
    {"label": "GPT-5.4-mini", "vendor": "OpenAI", "release": date(2026, 3, 5)},
    {"label": "GPT-5.4", "vendor": "OpenAI", "release": date(2026, 3, 5)},
    {"label": "Mistral-Small-4", "vendor": "Open weights", "release": date(2026, 3, 16)},
    {"label": "Kimi-K2.6", "vendor": "Open weights", "release": date(2026, 4, 20)},
    {"label": "GPT-5.5", "vendor": "OpenAI", "release": date(2026, 4, 23)},
    {"label": "DeepSeek-V4-pro", "vendor": "Open weights", "release": date(2026, 4, 24)},
    {"label": "Mistral-Medium-3.5", "vendor": "Open weights", "release": date(2026, 4, 30)},
    {"label": "Gemini-3.5-flash", "vendor": "Google", "release": date(2026, 5, 19)},
    {"label": "Opus 4.8", "vendor": "Anthropic", "release": date(2026, 5, 28)},
    {"label": "Fable 5", "vendor": "Anthropic", "release": date(2026, 6, 9)},
]

RESULTS = load_model_results()
for m in MODELS:
    m["correct"] = RESULTS[m["label"]]["correct"]
    m["side"] = RESULTS[m["label"]]["side_effects"]
    m["completion"] = 100 * m["correct"] / TOTAL_TASKS
    m["side_rate"] = 100 * m["side"] / TOTAL_TASKS

PLOT_STYLE = {
    "font.family": "serif",
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 13,
    "mathtext.fontset": "cm",
    "axes.linewidth": 0.9,
    "savefig.bbox": "tight",
}
plt.rcParams.update(PLOT_STYLE)
OUT = Path(__file__).parent


def _vendor_legend(ax: plt.Axes) -> None:
    handles = [
        plt.Line2D([], [], marker="o", linestyle="", color=c, markeredgecolor="white", markersize=9, label=v)
        for v, c in VENDOR_COLORS.items()
    ]
    ax.legend(handles=handles, frameon=False, fontsize=9, loc="upper right", ncol=2)


def plot_tradeoff() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    xs = np.array([m["completion"] for m in MODELS])
    ys = np.array([m["side_rate"] for m in MODELS])
    slope, intercept = np.polyfit(xs, ys, 1)
    grid = np.linspace(xs.min(), xs.max(), 100)
    ax.plot(grid, slope * grid + intercept, color="#999999", linestyle="--", linewidth=1.2, zorder=1)

    for m in MODELS:
        ax.scatter(
            m["completion"],
            m["side_rate"],
            s=130,
            color=VENDOR_COLORS[m["vendor"]],
            edgecolor="white",
            linewidth=1.2,
            zorder=3,
        )
        ax.annotate(
            m["label"],
            (m["completion"], m["side_rate"]),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=7.5,
            color="#222222",
            zorder=4,
        )

    ax.set_xlim(0, 100)
    ax.set_xlabel("Successful task completion (%)")
    ax.set_ylabel("Harmful side-effect rate (%)")
    ax.set_title("Capability vs. safety on WorkBench", pad=12)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.grid(True, color="#dddddd", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _vendor_legend(ax)
    fig.savefig(OUT / "side_effects_tradeoff.pdf")
    fig.savefig(OUT / "side_effects_tradeoff.png", dpi=220)
    plt.close(fig)


def plot_over_time() -> None:
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    frontier = []
    running_min = 1e9
    for m in sorted(MODELS, key=lambda m: m["release"]):
        if m["side_rate"] < running_min:
            frontier.append(m)
            running_min = m["side_rate"]
    ax.plot(
        [m["release"] for m in frontier],
        [m["side_rate"] for m in frontier],
        color="#888888",
        linewidth=1.2,
        alpha=0.5,
        zorder=2,
    )

    frontier_labels = {m["label"] for m in frontier}
    for m in MODELS:
        ax.scatter(
            m["release"],
            m["side_rate"],
            s=130,
            color=VENDOR_COLORS[m["vendor"]],
            edgecolor="white",
            linewidth=1.2,
            zorder=3,
        )
        if m["label"] in frontier_labels:
            ax.annotate(
                m["label"],
                (m["release"], m["side_rate"]),
                xytext=(6, 4),
                textcoords="offset points",
                fontsize=8,
                color="#222222",
                zorder=4,
            )

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylim(-2, 45)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("Model release date")
    ax.set_ylabel("Harmful side-effect rate (%)")
    ax.set_title("Harmful side effects on WorkBench over time", pad=12)
    ax.grid(True, color="#dddddd", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _vendor_legend(ax)
    fig.savefig(OUT / "side_effects_over_time.pdf")
    fig.savefig(OUT / "side_effects_over_time.png", dpi=220)
    plt.close(fig)


# The original 2024 GPT-4 result (43% completion, 26% side effects), scored with a
# ReAct loop on the pre-revision benchmark, shown alongside eight 2026 models.
OG_GPT4 = {"label": "GPT-4", "completion": 43.0, "side_rate": 26.0}
COMPOSITION_2026 = [
    "GPT-5.5",
    "Gemini-3.5-flash",
    "Gemini-3.1-pro",
    "Opus 4.8",
    "Sonnet 4.6",
    "Qwen3.5",
    "DeepSeek-V4-pro",
    "Fable 5",
]


def plot_composition() -> None:
    subset = [OG_GPT4] + [m for m in MODELS if m["label"] in COMPOSITION_2026]
    ordered = sorted(subset, key=lambda m: m["completion"])
    labels = [m["label"] for m in ordered]
    correct = np.array([m["completion"] for m in ordered])
    harm = np.array([m["side_rate"] for m in ordered])
    harmless = 100 - correct - harm

    fig, ax = plt.subplots(figsize=(7.8, 3.8))
    y = np.arange(len(ordered))
    ax.barh(y, correct, color=CORRECT_COLOR, label="Correct")
    ax.barh(y, harmless, left=correct, color=HARMLESS_COLOR, label="Failed, no harm")
    ax.barh(y, harm, left=correct + harmless, color=HARM_COLOR, label="Harmful side effect")

    sota = {"GPT-4": "2024 SOTA", "Fable 5": "2026 SOTA"}
    for i, m in enumerate(ordered):
        if m["label"] in sota:
            ax.text(102, i, sota[m["label"]], va="center", ha="left", fontsize=8.5, fontweight="bold", color="#444444")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, 124)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("Share of 690 tasks")
    ax.set_title("Outcome composition by model", pad=28)
    ax.legend(frameon=False, fontsize=9, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 1.01))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.invert_yaxis()
    fig.savefig(OUT / "side_effects_composition.pdf")
    fig.savefig(OUT / "side_effects_composition.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    plot_tradeoff()
    plot_over_time()
    plot_composition()
    print("wrote side_effects_tradeoff, side_effects_over_time, side_effects_composition (.pdf/.png)")
