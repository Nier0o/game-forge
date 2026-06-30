"""
Shared utilities: HTTP client, ObjectId generation, CSV saving, chart style.
"""
import csv
import secrets
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import requests

from config import GEN_SERVICE_SECRET

# ── Chart aesthetics ────────────────────────────────────────────────────────
BG    = "#0a0d1a"
FG    = "#d0d4e8"
GRID  = "#1a1f3a"
PALETTE = ["#00d2ff", "#f59e0b", "#6cf542", "#ff6b6b", "#c084fc", "#00ff88", "#ff9f00"]


def setup_style() -> None:
    plt.rcParams.update({
        "figure.facecolor":  BG,
        "axes.facecolor":    BG,
        "axes.edgecolor":    GRID,
        "axes.labelcolor":   FG,
        "axes.titlecolor":   FG,
        "xtick.color":       FG,
        "ytick.color":       FG,
        "text.color":        FG,
        "grid.color":        GRID,
        "grid.linestyle":    "--",
        "grid.alpha":        0.5,
        "legend.facecolor":  "#0d1226",
        "legend.edgecolor":  GRID,
        "font.size":         10,
    })


# ── HTTP ────────────────────────────────────────────────────────────────────

def headers() -> dict:
    h = {"Content-Type": "application/json"}
    if GEN_SERVICE_SECRET:
        h["x-gen-service-secret"] = GEN_SERVICE_SECRET
    return h


def post(url: str, payload: dict, timeout: int = 360) -> tuple[dict | None, float]:
    """POST payload to url. Returns (response_dict | None, elapsed_seconds)."""
    t0 = time.perf_counter()
    try:
        r = requests.post(url, json=payload, headers=headers(), timeout=timeout)
        elapsed = time.perf_counter() - t0
        if r.status_code >= 400:
            print(f"  [HTTP {r.status_code}] {url} — {r.text[:200]}")
            return None, elapsed
        return r.json(), elapsed
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        print(f"  [ERROR] {url} — {exc}")
        return None, elapsed


def get(url: str, timeout: int = 30) -> dict | None:
    try:
        r = requests.get(url, headers=headers(), timeout=timeout)
        if r.status_code >= 400:
            return None
        return r.json()
    except Exception:
        return None


# ── IDs ─────────────────────────────────────────────────────────────────────

def fake_objectid() -> str:
    """24-char hex string — valid MongoDB ObjectId format."""
    return secrets.token_hex(12)


def fake_uuid() -> str:
    import uuid
    return str(uuid.uuid4())


# ── Persistence ─────────────────────────────────────────────────────────────

def save_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  saved {path}")


def save_fig(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  saved {path}")


# ── Stats helpers ────────────────────────────────────────────────────────────

def mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def stdev(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = mean(vals)
    return (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5
