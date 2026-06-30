"""
bench_assets.py — Asset Generation Service: latency vs plan size.

Measures Stability AI throughput as entity count grows.
Each run generates sprites (1 per entity), background tiles (3),
a scene background, and a music track via the MCP server.

Expected duration per run: 2–8 minutes (depends on Stability AI latency).
Default ASSET_REPEAT=1.  Set ASSET_REPEAT=2+ for more reliable statistics.

Usage:
    python bench_assets.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent))
from config import ASSET_URL, ASSET_REPEAT, RESULTS_DIR, make_plan
from helpers import FG, post, fake_uuid, fake_objectid, save_csv, save_fig, setup_style, mean, stdev

OUT = RESULTS_DIR / "assets"

# Only test 3 sizes — each run is expensive (Stability AI calls)
ASSET_CONFIGS = [
    {"label": "Small  (2 enemies)",  "enemies": 2, "levels": 1},
    {"label": "Medium (4 enemies)",  "enemies": 4, "levels": 2},
    {"label": "Large  (6 enemies)",  "enemies": 6, "levels": 3},
]


def _expected_api_calls(n_enemies: int) -> int:
    """Estimate number of Stability AI API calls for a given enemy count."""
    n_entities = n_enemies + 2           # enemies + player + goal
    n_sprites  = n_entities               # one sprite per entity
    n_tiles    = 3                        # ground / platform / block
    n_bg       = 1                        # scene background
    n_music    = 1                        # theme music
    return n_sprites + n_tiles + n_bg + n_music


def run() -> list[dict]:
    rows = []
    for cfg in ASSET_CONFIGS:
        ne    = cfg["enemies"]
        nl    = cfg["levels"]
        label = cfg["label"]
        plan  = make_plan(ne, nl)
        n_api = _expected_api_calls(ne)
        print(f"\n  [{label}]  (~{n_api} Stability AI calls per run, {ASSET_REPEAT} run(s))")

        for run_i in range(1, ASSET_REPEAT + 1):
            game_id    = fake_uuid()
            project_id = fake_objectid()
            resp, elapsed = post(
                f"{ASSET_URL}/assets",
                {"gameId": game_id, "projectId": project_id, "plan": plan},
                timeout=900,  # 15 min hard cap
            )
            ok       = resp is not None and resp.get("status") == "ok"
            n_assets = len(resp.get("assets", [])) if ok else 0
            print(
                f"    run {run_i}: {'OK' if ok else 'FAIL'}  {elapsed:.1f}s  "
                f"{n_assets} assets  (~{elapsed / n_api:.1f}s per API call)"
            )
            rows.append({
                "label":           label,
                "n_enemies":       ne,
                "n_levels":        nl,
                "n_entities":      ne + 2,
                "expected_api_calls": n_api,
                "run":             run_i,
                "latency_s":       round(elapsed, 2),
                "n_assets_created": n_assets,
                "s_per_api_call":  round(elapsed / n_api, 2),
                "success":         ok,
            })
    return rows


# ── Charts ───────────────────────────────────────────────────────────────────

def chart_total_latency(rows: list[dict]) -> plt.Figure:
    setup_style()
    configs = ASSET_CONFIGS
    means_  = []
    stdevs_ = []
    labels  = []
    for cfg in configs:
        ok = [r for r in rows if r["label"] == cfg["label"] and r["success"]]
        lats = [r["latency_s"] for r in ok]
        means_.append(mean(lats))
        stdevs_.append(stdev(lats))
        labels.append(cfg["label"])

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: total latency bar chart
    ax = axes[0]
    x = range(len(labels))
    bars = ax.bar(x, means_, yerr=stdevs_, capsize=5,
                  color=["#00d2ff", "#f59e0b", "#6cf542"],
                  edgecolor="#0a0d1a",
                  error_kw={"color": "#ffffff88"})
    ax.bar_label(bars, labels=[f"{v:.0f}s" for v in means_], padding=5, color=FG)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=10, ha="right")
    ax.set_ylabel("Total latency (seconds)")
    ax.set_title("Total Asset Generation Time")
    ax.grid(axis="y")

    # Right: per-API-call latency
    ax2 = axes[1]
    per_call = [
        mean([r["s_per_api_call"] for r in rows if r["label"] == c["label"] and r["success"]])
        for c in configs
    ]
    entity_counts = [c["enemies"] + 2 for c in configs]
    ax2.plot(entity_counts, per_call, "o-", color="#c084fc", linewidth=2, markersize=8)
    for x_val, y_val in zip(entity_counts, per_call):
        ax2.annotate(
            f"{y_val:.1f}s", (x_val, y_val),
            textcoords="offset points", xytext=(0, 8),
            ha="center", color="#c084fc",
        )
    ax2.set_xlabel("Total entity count")
    ax2.set_ylabel("Mean seconds per Stability AI call")
    ax2.set_title("Per-API-Call Latency vs Entity Count")
    ax2.grid()

    fig.suptitle("Asset Generation Service — Stability AI Throughput", y=1.01)
    fig.tight_layout()
    return fig


def print_summary(rows: list[dict]) -> None:
    table = []
    for cfg in ASSET_CONFIGS:
        ok  = [r for r in rows if r["label"] == cfg["label"] and r["success"]]
        all_ = [r for r in rows if r["label"] == cfg["label"]]
        lats = [r["latency_s"] for r in ok]
        per  = [r["s_per_api_call"] for r in ok]
        n_api = cfg["enemies"] + 2 + 3 + 1 + 1  # sprites + tiles + bg + music
        table.append([
            cfg["label"],
            cfg["enemies"] + 2,
            n_api,
            len(ok),
            f"{mean(lats):.0f} ± {stdev(lats):.0f}s" if lats else "N/A",
            f"{mean(per):.1f}s" if per else "N/A",
        ])
    print("\n" + tabulate(
        table,
        headers=["Config", "Entities", "API Calls", "OK Runs",
                 "Total Latency", "Avg s/API Call"],
        tablefmt="rounded_outline",
    ))


def main() -> list[dict]:
    print("=" * 60)
    print("  BENCHMARK: Asset Generation — Stability AI Latency")
    print("=" * 60)
    print("  Note: each run takes 2–8 minutes and uses Stability AI credits.")

    rows = run()
    if not rows:
        print("  No results collected.")
        return []

    save_csv(rows, OUT / "data.csv")
    save_fig(chart_total_latency(rows), OUT / "latency.png")
    print_summary(rows)
    return rows


if __name__ == "__main__":
    main()
