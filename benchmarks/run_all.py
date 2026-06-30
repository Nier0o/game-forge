"""
run_all.py — Orchestrator: runs all 4 benchmarks and prints a combined summary.

Order:
  1. bench_planner  (fast, ~1-3 min)
  2. bench_code     (fast, ~2-5 min)
  3. bench_assets   (slow, ~2-8 min per run × ASSET_REPEAT)
  4. bench_e2e      (slowest, full pipeline × E2E_REPEAT per prompt)

Flags (env vars):
  SKIP_PLANNER=1   Skip the planner benchmark
  SKIP_CODE=1      Skip the code benchmark
  SKIP_ASSETS=1    Skip the asset benchmark (saves Stability AI credits)
  SKIP_E2E=1       Skip the E2E benchmark

Usage:
    cd game-forge/benchmarks
    pip install -r requirements.txt
    python run_all.py

    # Skip the expensive stages during development:
    SKIP_ASSETS=1 SKIP_E2E=1 python run_all.py
"""
import os
import sys
import time
from pathlib import Path

from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent))
from helpers import get
from config import (
    PLANNER_URL, ASSET_URL, CODE_URL, BUILDER_URL,
    BENCH_REPEAT, ASSET_REPEAT, E2E_REPEAT, RESULTS_DIR,
)

SKIP_PLANNER = os.getenv("SKIP_PLANNER", "0") == "1"
SKIP_CODE    = os.getenv("SKIP_CODE",    "0") == "1"
SKIP_ASSETS  = os.getenv("SKIP_ASSETS",  "0") == "1"
SKIP_E2E     = os.getenv("SKIP_E2E",     "0") == "1"


def check_health() -> bool:
    """Verify all 4 services respond on /health before starting."""
    services = [
        ("Planner",  PLANNER_URL),
        ("Asset",    ASSET_URL),
        ("Code",     CODE_URL),
        ("Builder",  BUILDER_URL),
    ]
    all_ok = True
    print("\n── Health checks ─────────────────────────────────────────")
    for name, base in services:
        resp = get(f"{base}/health", timeout=5)
        ok   = resp is not None and resp.get("status") == "ok"
        sym  = "✓" if ok else "✗"
        print(f"  {sym} {name:10s}  {base}/health  {'OK' if ok else 'UNREACHABLE'}")
        if not ok:
            all_ok = False
    return all_ok


def run_benchmark(name: str, module_name: str, skipped: bool) -> dict | None:
    if skipped:
        print(f"\n── {name}  [SKIPPED] ────────────────────────────────────")
        return None
    print(f"\n── {name} ────────────────────────────────────────────────")
    t0 = time.perf_counter()
    mod = __import__(module_name)
    rows = mod.main()
    elapsed = time.perf_counter() - t0
    print(f"\n  Finished in {elapsed:.0f}s  ({len(rows or [])} data points)")
    return {"rows": rows or [], "elapsed_s": elapsed}


def print_combined_summary(results: dict) -> None:
    print("\n" + "=" * 60)
    print("  COMBINED BENCHMARK SUMMARY")
    print("=" * 60)

    summary_rows = []

    if "planner" in results and results["planner"]:
        rows = results["planner"]["rows"]
        ok   = [r for r in rows if r.get("success")]
        lats = [r["latency_s"] for r in ok]
        quality = (
            sum(
                sum(r.get(k, 0) for k in [
                    "valid_archetype", "correct_archetype", "has_title",
                    "one_player", "min_entities", "all_described",
                    "valid_win_cond", "valid_theme", "valid_style", "has_audio",
                ])
                for r in ok
            ) / (len(ok) * 10)
            if ok else 0
        )
        from helpers import mean as _mean, stdev as _stdev
        summary_rows.append([
            "Planner",
            f"{len(ok)}/{len(rows)}",
            f"{_mean(lats):.1f} ± {_stdev(lats):.1f}s" if lats else "N/A",
            f"{quality:.0%} quality score",
        ])

    if "code" in results and results["code"]:
        rows = results["code"]["rows"]
        ok   = [r for r in rows if r.get("success")]
        lats = [r["latency_s"] for r in ok]
        from helpers import mean as _mean, stdev as _stdev
        summary_rows.append([
            "Code Assembly",
            f"{len(ok)}/{len(rows)}",
            f"{_mean(lats):.2f} ± {_stdev(lats):.2f}s" if lats else "N/A",
            "No external deps (MinIO only)",
        ])

    if "assets" in results and results["assets"]:
        rows = results["assets"]["rows"]
        ok   = [r for r in rows if r.get("success")]
        lats = [r["latency_s"] for r in ok]
        per  = [r["s_per_api_call"] for r in ok]
        from helpers import mean as _mean, stdev as _stdev
        summary_rows.append([
            "Asset Generation",
            f"{len(ok)}/{len(rows)}",
            f"{_mean(lats):.0f} ± {_stdev(lats):.0f}s" if lats else "N/A",
            f"{_mean(per):.1f}s/API call avg" if per else "N/A",
        ])

    if "e2e" in results and results["e2e"]:
        rows = results["e2e"]["rows"]
        ok   = [r for r in rows if r.get("ok")]
        totals = [r["total_s"] for r in ok]
        from helpers import mean as _mean, stdev as _stdev
        import numpy as np
        p50 = f"{np.percentile(totals, 50):.0f}s" if totals else "N/A"
        p90 = f"{np.percentile(totals, 90):.0f}s" if totals else "N/A"
        summary_rows.append([
            "End-to-End Pipeline",
            f"{len(ok)}/{len(rows)}",
            f"p50={p50} p90={p90}",
            f"mean {_mean(totals):.0f}s" if totals else "N/A",
        ])

    print(tabulate(
        summary_rows,
        headers=["Service", "OK/Total", "Latency", "Notes"],
        tablefmt="rounded_outline",
    ))

    print(f"\n  Results saved in: {RESULTS_DIR.resolve()}")
    print("  Charts: results/<service>/*.png")


def main() -> None:
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         Game-Forge Performance Benchmark Suite           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"\n  Settings:")
    print(f"    BENCH_REPEAT  = {BENCH_REPEAT}  (planner / code runs per config)")
    print(f"    ASSET_REPEAT  = {ASSET_REPEAT}  (asset runs per config)")
    print(f"    E2E_REPEAT    = {E2E_REPEAT}  (E2E runs per prompt)")
    print(f"    RESULTS_DIR   = {RESULTS_DIR}")

    if not check_health():
        print("\n  ⚠  One or more services are unreachable.")
        print("     Make sure `docker compose up -d` is running, then retry.")
        sys.exit(1)

    wall_start = time.perf_counter()
    results = {}

    results["planner"] = run_benchmark(
        "Planner Quality & Latency", "bench_planner", SKIP_PLANNER
    )
    results["code"] = run_benchmark(
        "Code Assembly Throughput",  "bench_code",    SKIP_CODE
    )
    results["assets"] = run_benchmark(
        "Asset Generation Latency",  "bench_assets",  SKIP_ASSETS
    )
    results["e2e"] = run_benchmark(
        "End-to-End Pipeline",       "bench_e2e",     SKIP_E2E
    )

    print_combined_summary(results)
    print(f"\n  Total wall time: {time.perf_counter() - wall_start:.0f}s")


if __name__ == "__main__":
    main()
