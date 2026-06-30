"""
bench_code.py — Code Assembly Service: throughput vs plan complexity.

Measures how assembly time scales with the number of entities and levels.
The code service (game-forge-code) is purely local computation + MinIO upload —
no LLM, no Stability AI — so this benchmark runs quickly (seconds per call).

Calls POST /code for each (enemy_count × level_count) combination BENCH_REPEAT times.

Output:
  results/code/data.csv
  results/code/throughput.png    — grouped bar chart, entities on x-axis, grouped by level count
  results/code/heatmap.png       — mean assembly time as a heat-table

Usage:
    python bench_code.py
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent))
from config import CODE_URL, BENCH_REPEAT, RESULTS_DIR, PLAN_SIZES, make_plan
from helpers import post, fake_uuid, save_csv, save_fig, setup_style, mean, stdev

OUT = RESULTS_DIR / "code"

# Test matrix: (n_enemies, n_levels) pairs
CONFIGS = [
    (2, 1), (2, 2), (2, 3),
    (4, 1), (4, 2), (4, 3),
    (6, 1), (6, 2), (6, 3),
    (8, 1), (8, 2), (8, 3),
]


def run() -> list[dict]:
    rows = []
    for (n_enemies, n_levels) in CONFIGS:
        label = f"{n_enemies}e / {n_levels}L"
        plan  = make_plan(n_enemies, n_levels)
        print(f"\n  [{label}]  ({BENCH_REPEAT} run(s))")
        for run_i in range(1, BENCH_REPEAT + 1):
            game_id = fake_uuid()
            resp, elapsed = post(
                f"{CODE_URL}/code",
                {"gameId": game_id, "plan": plan},
                timeout=120,
            )
            ok = resp is not None and resp.get("status") == "ok"
            n_keys = len(resp.get("scriptKeys", [])) if ok else 0
            print(f"    run {run_i}: {'OK' if ok else 'FAIL'}  {elapsed:.2f}s  {n_keys} files")
            rows.append({
                "n_enemies":    n_enemies,
                "n_levels":     n_levels,
                "n_entities":   n_enemies + 2,  # player + enemies + goal
                "label":        label,
                "run":          run_i,
                "latency_s":    round(elapsed, 3),
                "n_script_keys": n_keys,
                "success":      ok,
            })
    return rows


# ── Charts ───────────────────────────────────────────────────────────────────

def chart_grouped_bars(rows: list[dict]) -> plt.Figure:
    setup_style()
    enemy_counts = sorted({r["n_enemies"] for r in rows})
    level_counts = sorted({r["n_levels"] for r in rows})
    colors = ["#00d2ff", "#f59e0b", "#6cf542"]

    x = np.arange(len(enemy_counts))
    width = 0.22
    offsets = np.linspace(-(len(level_counts) - 1) * width / 2,
                          (len(level_counts) - 1) * width / 2,
                          len(level_counts))

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, nl in enumerate(level_counts):
        means_ = []
        errs_  = []
        for ne in enemy_counts:
            vals = [
                r["latency_s"] for r in rows
                if r["n_enemies"] == ne and r["n_levels"] == nl and r["success"]
            ]
            means_.append(mean(vals))
            errs_.append(stdev(vals))
        bars = ax.bar(
            x + offsets[i], means_, width, label=f"{nl} level(s)",
            color=colors[i % len(colors)], edgecolor="#0a0d1a",
            yerr=errs_, capsize=4, error_kw={"color": "#ffffff88"},
        )
        ax.bar_label(bars, labels=[f"{v:.1f}s" for v in means_], padding=3,
                     fontsize=7, color=colors[i % len(colors)])

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{ne} enemies\n({ne + 2} entities)" for ne in enemy_counts])
    ax.set_ylabel("Mean assembly latency (seconds)")
    ax.set_title("Code Assembly Service — Throughput vs Plan Complexity")
    ax.legend(title="Level count")
    ax.grid(axis="y")
    fig.tight_layout()
    return fig


def chart_heatmap(rows: list[dict]) -> plt.Figure:
    setup_style()
    enemy_counts = sorted({r["n_enemies"] for r in rows})
    level_counts = sorted({r["n_levels"] for r in rows})

    matrix = np.zeros((len(level_counts), len(enemy_counts)))
    for j, ne in enumerate(enemy_counts):
        for i, nl in enumerate(level_counts):
            vals = [
                r["latency_s"] for r in rows
                if r["n_enemies"] == ne and r["n_levels"] == nl and r["success"]
            ]
            matrix[i, j] = mean(vals)

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(enemy_counts)))
    ax.set_xticklabels([f"{ne}e" for ne in enemy_counts])
    ax.set_yticks(range(len(level_counts)))
    ax.set_yticklabels([f"{nl}L" for nl in level_counts])
    ax.set_xlabel("Enemy count")
    ax.set_ylabel("Level count")
    for j in range(len(enemy_counts)):
        for i in range(len(level_counts)):
            ax.text(j, i, f"{matrix[i, j]:.2f}s", ha="center", va="center",
                    fontsize=9, color="black" if matrix[i, j] > matrix.max() * 0.5 else "white")
    fig.colorbar(im, ax=ax, label="Latency (s)")
    ax.set_title("Code Service Latency Heat-Table")
    fig.tight_layout()
    return fig


def print_summary(rows: list[dict]) -> None:
    table = []
    for (ne, nl) in CONFIGS:
        ok   = [r for r in rows if r["n_enemies"] == ne and r["n_levels"] == nl and r["success"]]
        all_ = [r for r in rows if r["n_enemies"] == ne and r["n_levels"] == nl]
        lats = [r["latency_s"] for r in ok]
        keys = [r["n_script_keys"] for r in ok]
        table.append([
            f"{ne} enemies / {nl} levels",
            ne + 2,
            len(ok),
            f"{mean(lats):.2f} ± {stdev(lats):.2f}s" if lats else "N/A",
            int(mean(keys)) if keys else 0,
        ])
    print("\n" + tabulate(
        table,
        headers=["Config", "Total Entities", "Successful Runs", "Latency (mean±std)", "Avg Files"],
        tablefmt="rounded_outline",
    ))


def main() -> list[dict]:
    print("=" * 60)
    print("  BENCHMARK: Code Assembly Service — Throughput")
    print("=" * 60)

    rows = run()
    if not rows:
        print("  No results collected.")
        return []

    save_csv(rows, OUT / "data.csv")
    save_fig(chart_grouped_bars(rows), OUT / "throughput.png")
    save_fig(chart_heatmap(rows), OUT / "heatmap.png")
    print_summary(rows)
    return rows


if __name__ == "__main__":
    main()
