"""
bench_planner.py — Planner Service: latency and output quality evaluation.

Calls POST /plan for each benchmark prompt (BENCH_REPEAT times each).
Scores the returned GamePlan against 10 quality criteria, then plots:
  - latency bar chart (mean ± std per prompt)
  - quality heatmap  (pass rate per criterion × prompt)

Usage:
    python bench_planner.py
"""
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent))
from config import PLANNER_URL, BENCH_REPEAT, RESULTS_DIR, PROMPTS
from helpers import post, fake_objectid, save_csv, save_fig, setup_style, mean, stdev

OUT = RESULTS_DIR / "planner"

# ── Quality rubric ───────────────────────────────────────────────────────────

VALID_ARCHETYPES = {"platformer", "top-down", "endless-runner"}
VALID_STYLES     = {"pixel", "anime", "realistic", "cartoon", "lowpoly",
                    "painterly", "handdrawn", "cyberpunk", "fantasy"}
VALID_WIN = {
    "platformer":     {"reach_door", "collect_all", "defeat_all", "score_target"},
    "top-down":       {"reach_door", "collect_all", "defeat_all", "score_target"},
    "endless-runner": {"survive_time", "score_target", "collect_all", "defeat_all"},
}
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
THEME_FIELDS = ("background_color", "accent_color", "ground_color", "hazard_color")

CRITERIA = {
    "valid_archetype":   "Archetype is a known value",
    "correct_archetype": "Archetype matches prompt intent",
    "has_title":         "Non-empty title present",
    "one_player":        "Exactly 1 player entity",
    "min_entities":      "≥ 2 entities total",
    "all_described":     "All entities have visualDescription",
    "valid_win_cond":    "Win condition valid for archetype",
    "valid_theme":       "Theme has 4 valid hex colours",
    "valid_style":       "Style is a known value",
    "has_audio":         "≥ 1 sound effect in audio",
}


def score_plan(plan: dict, expected_archetype: str) -> dict[str, int]:
    archetype = plan.get("archetype", "")
    entities  = plan.get("entities", [])
    players   = [e for e in entities if e.get("type") == "player"]
    theme     = plan.get("theme", {})
    params    = plan.get("parameters", {})
    wc        = params.get("win_condition_type", "")
    audio     = plan.get("audio", {})

    valid_wins = VALID_WIN.get(archetype, set())

    return {
        "valid_archetype":   int(archetype in VALID_ARCHETYPES),
        "correct_archetype": int(archetype == expected_archetype),
        "has_title":         int(bool(str(plan.get("title", "")).strip())),
        "one_player":        int(len(players) == 1),
        "min_entities":      int(len(entities) >= 2),
        "all_described":     int(
            all(e.get("visualDescription") for e in entities) and bool(entities)
        ),
        "valid_win_cond":    int(wc in valid_wins),
        "valid_theme":       int(
            all(HEX_RE.match(str(theme.get(f, ""))) for f in THEME_FIELDS)
        ),
        "valid_style":       int(plan.get("style", "") in VALID_STYLES),
        "has_audio":         int(len(audio.get("soundEffects", [])) >= 1),
    }


# ── Benchmark runner ─────────────────────────────────────────────────────────

def run() -> list[dict]:
    rows = []
    for p in PROMPTS:
        print(f"\n  [{p['name']}]  ({BENCH_REPEAT} run(s))")
        for run_i in range(1, BENCH_REPEAT + 1):
            project_id = fake_objectid()
            resp, elapsed = post(
                f"{PLANNER_URL}/plan",
                {"prompt": p["prompt"], "projectId": project_id},
                timeout=120,
            )

            if resp is None or resp.get("status") != "ok":
                print(f"    run {run_i}: FAILED ({elapsed:.1f}s)")
                rows.append({
                    "prompt_id": p["id"], "prompt_name": p["name"],
                    "run": run_i, "latency_s": round(elapsed, 3),
                    "success": False,
                    **{k: 0 for k in CRITERIA},
                })
                continue

            plan    = resp.get("plan", {})
            scores  = score_plan(plan, p["archetype"])
            total   = sum(scores.values())
            print(
                f"    run {run_i}: {elapsed:.1f}s  quality {total}/{len(CRITERIA)}"
                f"  archetype={plan.get('archetype')}  entities={len(plan.get('entities', []))}"
            )
            rows.append({
                "prompt_id":   p["id"],
                "prompt_name": p["name"],
                "run":         run_i,
                "latency_s":   round(elapsed, 3),
                "success":     True,
                **scores,
            })
    return rows


# ── Charts ───────────────────────────────────────────────────────────────────

def chart_latency(rows: list[dict]) -> plt.Figure:
    setup_style()
    names   = [p["name"] for p in PROMPTS]
    means_  = []
    stdevs_ = []
    for p in PROMPTS:
        vals = [r["latency_s"] for r in rows if r["prompt_id"] == p["id"] and r["success"]]
        means_.append(mean(vals))
        stdevs_.append(stdev(vals))

    fig, ax = plt.subplots(figsize=(9, 4))
    x = range(len(names))
    bars = ax.bar(x, means_, yerr=stdevs_, capsize=5,
                  color="#00d2ff", edgecolor="#0a0d1a", linewidth=0.8, error_kw={"color": "#f59e0b"})
    ax.bar_label(bars, labels=[f"{v:.1f}s" for v in means_], padding=4, color="#f59e0b", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.set_ylabel("Mean latency (seconds)")
    ax.set_title("Planner Service — Response Latency per Prompt")
    ax.grid(axis="y")
    ax.set_ylim(0, max(means_) * 1.3 if means_ else 10)
    fig.tight_layout()
    return fig


def chart_quality(rows: list[dict]) -> plt.Figure:
    setup_style()
    crit_keys = list(CRITERIA.keys())
    crit_labels = [CRITERIA[k] for k in crit_keys]
    prompt_names = [p["name"] for p in PROMPTS]

    matrix = np.zeros((len(crit_keys), len(PROMPTS)))
    for j, p in enumerate(PROMPTS):
        p_rows = [r for r in rows if r["prompt_id"] == p["id"] and r["success"]]
        if not p_rows:
            continue
        for i, k in enumerate(crit_keys):
            matrix[i, j] = mean([r[k] for r in p_rows])

    fig, ax = plt.subplots(figsize=(10, 5))
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "rg", ["#cc2200", "#ffaa00", "#00aa44"]
    )
    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(prompt_names)))
    ax.set_xticklabels(prompt_names, rotation=20, ha="right")
    ax.set_yticks(range(len(crit_labels)))
    ax.set_yticklabels(crit_labels)
    for i in range(len(crit_keys)):
        for j in range(len(PROMPTS)):
            v = matrix[i, j]
            ax.text(j, i, f"{v:.0%}", ha="center", va="center",
                    color="white" if v < 0.6 else "#0a0d1a", fontsize=8, fontweight="bold")
    fig.colorbar(im, ax=ax, label="Pass rate (1 = always passes)")
    ax.set_title("Planner Service — Quality Criteria Pass Rate")
    fig.tight_layout()
    return fig


# ── Summary table ─────────────────────────────────────────────────────────────

def print_summary(rows: list[dict]) -> None:
    table = []
    for p in PROMPTS:
        p_rows = [r for r in rows if r["prompt_id"] == p["id"]]
        ok     = [r for r in p_rows if r["success"]]
        lats   = [r["latency_s"] for r in ok]
        quality = (
            mean([sum(r[k] for k in CRITERIA) for r in ok]) / len(CRITERIA)
            if ok else 0
        )
        table.append([
            p["name"],
            len(p_rows),
            len(ok),
            f"{mean(lats):.1f} ± {stdev(lats):.1f}s" if lats else "N/A",
            f"{quality:.0%}",
        ])
    print("\n" + tabulate(
        table,
        headers=["Prompt", "Runs", "OK", "Latency (mean±std)", "Quality"],
        tablefmt="rounded_outline",
    ))


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> list[dict]:
    print("=" * 60)
    print("  BENCHMARK: Planner Service — Latency & Quality")
    print("=" * 60)

    rows = run()
    if not rows:
        print("  No results collected.")
        return []

    save_csv(rows, OUT / "data.csv")
    save_fig(chart_latency(rows), OUT / "latency.png")
    save_fig(chart_quality(rows), OUT / "quality_heatmap.png")
    print_summary(rows)
    return rows


if __name__ == "__main__":
    main()
