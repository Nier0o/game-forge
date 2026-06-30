"""
bench_e2e.py — End-to-End Pipeline: latency breakdown across all 4 services.

Chains the 4 microservices directly (bypassing the frontend chat flow) to
measure where the total generation time is spent:

  planner (/plan) → code+asset in parallel → builder (/build)

Each pipeline run produces one playable HTML5 game stub (SKIP_GODOT_EXPORT=true)
or a real Godot HTML5 export (SKIP_GODOT_EXPORT=false, Godot must be installed).

Requires: MinIO, MongoDB, all 4 worker services, and assets-mcp reachable.

Output:
  results/e2e/data.csv
  results/e2e/stage_breakdown.png   — stacked horizontal bar per prompt
  results/e2e/cdf.png               — CDF of total latency across all runs

Usage:
    python bench_e2e.py
"""
import sys
import threading
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    PLANNER_URL, ASSET_URL, CODE_URL, BUILDER_URL,
    E2E_REPEAT, RESULTS_DIR, PROMPTS,
)
from helpers import post, fake_uuid, fake_objectid, save_csv, save_fig, setup_style, mean, stdev

OUT = RESULTS_DIR / "e2e"

STAGE_COLORS = {
    "planner":  "#00d2ff",
    "parallel": "#f59e0b",
    "builder":  "#6cf542",
}
STAGE_ORDER = ["planner", "parallel", "builder"]


def run_pipeline(prompt_text: str, project_id: str) -> dict:
    """
    Execute one full pipeline for the given prompt.
    Returns a dict with stage latencies and overall success.
    """
    game_id  = fake_uuid()
    build_id = fake_objectid()

    # ── Stage 1: Planner ────────────────────────────────────────────────────
    planner_resp, t_planner = post(
        f"{PLANNER_URL}/plan",
        {"prompt": prompt_text, "projectId": project_id},
        timeout=120,
    )
    if planner_resp is None or planner_resp.get("status") != "ok":
        return {"ok": False, "stage_failed": "planner",
                "planner_s": t_planner, "parallel_s": 0, "builder_s": 0, "total_s": t_planner,
                "game_id": game_id}

    plan = planner_resp["plan"]

    # ── Stage 2: Code + Asset in parallel ───────────────────────────────────
    code_result   = {}
    asset_result  = {}

    def call_code():
        resp, elapsed = post(
            f"{CODE_URL}/code",
            {"gameId": game_id, "plan": plan},
            timeout=120,
        )
        code_result["resp"]    = resp
        code_result["elapsed"] = elapsed

    def call_assets():
        resp, elapsed = post(
            f"{ASSET_URL}/assets",
            {"gameId": game_id, "projectId": project_id, "plan": plan},
            timeout=900,
        )
        asset_result["resp"]    = resp
        asset_result["elapsed"] = elapsed

    t_code   = threading.Thread(target=call_code,   daemon=True)
    t_assets = threading.Thread(target=call_assets, daemon=True)
    t_code.start()
    t_assets.start()
    t_code.join()
    t_assets.join()

    t_parallel = max(code_result.get("elapsed", 0), asset_result.get("elapsed", 0))
    code_ok    = code_result.get("resp", {}) and code_result["resp"].get("status") == "ok"
    asset_ok   = asset_result.get("resp", {}) and asset_result["resp"].get("status") == "ok"

    asset_docs = asset_result["resp"].get("assets", []) if asset_ok else []

    # ── Stage 3: Builder ────────────────────────────────────────────────────
    builder_resp, t_builder = post(
        f"{BUILDER_URL}/build",
        {"gameId": game_id, "plan": plan, "assetDocs": asset_docs, "buildId": build_id},
        timeout=600,
    )
    build_ok = builder_resp is not None and builder_resp.get("status") == "ok"

    total_s = t_planner + t_parallel + t_builder

    return {
        "ok":         build_ok,
        "game_id":    game_id,
        "planner_s":  round(t_planner,  2),
        "parallel_s": round(t_parallel, 2),
        "builder_s":  round(t_builder,  2),
        "total_s":    round(total_s,    2),
        "code_ok":    code_ok,
        "asset_ok":   asset_ok,
        "build_ok":   build_ok,
        "stage_failed": (
            "builder" if not build_ok
            else "code" if not code_ok
            else "asset" if not asset_ok
            else None
        ),
    }


def run() -> list[dict]:
    rows = []
    for p in PROMPTS:
        print(f"\n  [{p['name']}]  ({E2E_REPEAT} run(s))")
        project_id = fake_objectid()
        for run_i in range(1, E2E_REPEAT + 1):
            print(f"    run {run_i}: running pipeline…", flush=True)
            result = run_pipeline(p["prompt"], project_id)
            print(
                f"    run {run_i}: {'OK' if result['ok'] else 'FAIL (' + str(result.get('stage_failed')) + ')'}"
                f"  total={result['total_s']:.1f}s"
                f"  planner={result['planner_s']:.1f}s"
                f"  parallel={result['parallel_s']:.1f}s"
                f"  builder={result['builder_s']:.1f}s"
            )
            rows.append({
                "prompt_id":   p["id"],
                "prompt_name": p["name"],
                "run":         run_i,
                **{k: result[k] for k in
                   ("ok", "planner_s", "parallel_s", "builder_s", "total_s",
                    "code_ok", "asset_ok", "build_ok", "stage_failed", "game_id")},
            })
    return rows


# ── Charts ───────────────────────────────────────────────────────────────────

def chart_stage_breakdown(rows: list[dict]) -> plt.Figure:
    setup_style()
    prompt_names = [p["name"] for p in PROMPTS]
    stage_means  = {s: [] for s in STAGE_ORDER}

    for p in PROMPTS:
        ok = [r for r in rows if r["prompt_id"] == p["id"] and r["ok"]]
        for s in STAGE_ORDER:
            vals = [r[f"{s}_s"] for r in ok]
            stage_means[s].append(mean(vals))

    fig, ax = plt.subplots(figsize=(10, 5))
    y   = np.arange(len(prompt_names))
    lefts = np.zeros(len(prompt_names))

    for stage in STAGE_ORDER:
        vals = np.array(stage_means[stage])
        bars = ax.barh(y, vals, left=lefts, label=stage.capitalize(),
                       color=STAGE_COLORS[stage], edgecolor="#0a0d1a", height=0.55)
        for bar, v in zip(bars, vals):
            if v > 2:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{v:.0f}s", ha="center", va="center",
                    color="#0a0d1a", fontsize=8, fontweight="bold",
                )
        lefts += vals

    # Total labels on the right
    for i, total in enumerate(lefts):
        ax.text(total + 1, i, f"{total:.0f}s total",
                va="center", color="#d0d4e8", fontsize=9)

    ax.set_yticks(list(y))
    ax.set_yticklabels(prompt_names)
    ax.set_xlabel("Time (seconds)")
    ax.set_title("End-to-End Pipeline — Stage Breakdown per Prompt")
    ax.legend(loc="lower right")
    ax.grid(axis="x")
    ax.set_xlim(0, lefts.max() * 1.2)
    fig.tight_layout()
    return fig


def chart_cdf(rows: list[dict]) -> plt.Figure:
    setup_style()
    ok_totals = sorted([r["total_s"] for r in rows if r["ok"]])
    if not ok_totals:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No successful runs", ha="center", va="center", transform=ax.transAxes)
        return fig

    cdf = np.arange(1, len(ok_totals) + 1) / len(ok_totals)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.step(ok_totals, cdf, where="post", color="#c084fc", linewidth=2)
    ax.fill_between(ok_totals, cdf, step="post", alpha=0.15, color="#c084fc")

    p50 = np.percentile(ok_totals, 50)
    p90 = np.percentile(ok_totals, 90)
    ax.axvline(p50, color="#f59e0b", linestyle="--", label=f"p50 = {p50:.0f}s")
    ax.axvline(p90, color="#ff6b6b", linestyle="--", label=f"p90 = {p90:.0f}s")

    ax.set_xlabel("Total pipeline latency (seconds)")
    ax.set_ylabel("Cumulative fraction of runs")
    ax.set_title("Pipeline Latency CDF (all prompts combined)")
    ax.legend()
    ax.grid()
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    return fig


def print_summary(rows: list[dict]) -> None:
    table = []
    for p in PROMPTS:
        p_rows = [r for r in rows if r["prompt_id"] == p["id"]]
        ok     = [r for r in p_rows if r["ok"]]
        def m(key):
            vals = [r[key] for r in ok]
            return f"{mean(vals):.0f}s" if vals else "N/A"
        table.append([
            p["name"],
            f"{len(ok)}/{len(p_rows)}",
            m("total_s"),
            m("planner_s"),
            m("parallel_s"),
            m("builder_s"),
        ])
    print("\n" + tabulate(
        table,
        headers=["Prompt", "OK/Runs", "Total", "Planner", "Code+Asset", "Builder"],
        tablefmt="rounded_outline",
    ))


def main() -> list[dict]:
    print("=" * 60)
    print("  BENCHMARK: End-to-End Pipeline — Stage Breakdown")
    print("=" * 60)
    print("  Chaining: planner → (code + asset in parallel) → builder")
    print("  Note: asset stage calls Stability AI (~2-8 min per run)")

    rows = run()
    if not rows:
        print("  No results collected.")
        return []

    save_csv(rows, OUT / "data.csv")
    save_fig(chart_stage_breakdown(rows), OUT / "stage_breakdown.png")
    save_fig(chart_cdf(rows), OUT / "cdf.png")
    print_summary(rows)
    return rows


if __name__ == "__main__":
    main()
