"""
Benchmark configuration — edit here or override via environment variables.
"""
import os
from pathlib import Path

# ── Service base URLs (docker-compose published ports) ──────────────────────
PLANNER_URL = os.getenv("PLANNER_URL",  "http://localhost:6101")
ASSET_URL   = os.getenv("ASSET_URL",    "http://localhost:6102")
CODE_URL    = os.getenv("CODE_URL",     "http://localhost:6103")
BUILDER_URL = os.getenv("BUILDER_URL",  "http://localhost:6104")

# ── Inter-service auth (from GEN_SERVICE_SECRET in .env) ────────────────────
GEN_SERVICE_SECRET = os.getenv("GEN_SERVICE_SECRET", "")

# ── Run counts (lower = faster; higher = more reliable statistics) ───────────
BENCH_REPEAT  = int(os.getenv("BENCH_REPEAT",  "3"))  # planner / code runs per config
ASSET_REPEAT  = int(os.getenv("ASSET_REPEAT",  "1"))  # asset runs per config (each is ~2-6 min)
E2E_REPEAT    = int(os.getenv("E2E_REPEAT",    "2"))  # E2E runs per prompt (each is ~3-10 min)

# ── Output directory (created automatically) ────────────────────────────────
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "results"))

# ── Benchmark prompts — one per archetype plus two richer variants ───────────
PROMPTS = [
    {
        "id":        "simple_platformer",
        "name":      "Simple Platformer",
        "archetype": "platformer",
        "prompt": (
            "A 2-level platformer where a knight collects coins and defeats slimes "
            "to reach the exit door at the end of each level"
        ),
    },
    {
        "id":        "dungeon_topdown",
        "name":      "Dungeon Crawler",
        "archetype": "top-down",
        "prompt": (
            "A top-down dungeon crawler where a hero fights skeleton guards and "
            "collects gold coins across 2 rooms to reach the exit portal"
        ),
    },
    {
        "id":        "endless_runner",
        "name":      "Endless Runner",
        "archetype": "endless-runner",
        "prompt": (
            "An endless runner where a flying bird dodges moving pipes and "
            "collects golden stars to survive as long as possible"
        ),
    },
    {
        "id":        "boss_fight",
        "name":      "Boss Fight",
        "archetype": "platformer",
        "prompt": (
            "A 3-level platformer: fight goblins in a cave in level 1, "
            "skeletons in a haunted forest in level 2, then defeat a dragon boss in level 3"
        ),
    },
    {
        "id":        "space_shooter",
        "name":      "Space Shooter",
        "archetype": "top-down",
        "prompt": (
            "A top-down space shooter where a spaceship fights alien waves across "
            "2 levels then destroys an alien mothership boss to win"
        ),
    },
]

# ── Synthetic plan builder for asset / code / builder benchmarks ─────────────

VALID_WIN_CONDITION = {
    "platformer":     "reach_door",
    "top-down":       "defeat_all",
    "endless-runner": "survive_time",
}


def make_plan(n_enemies: int, n_levels: int, archetype: str = "platformer") -> dict:
    """Minimal but valid GamePlan with `n_enemies` enemies + 1 player + 1 goal."""
    entities = [
        {
            "name": "hero",
            "type": "player",
            "visualDescription": "a brave pixel-art knight in silver armour",
            "size": "medium",
            "behaviors": [],
        }
    ]
    for i in range(n_enemies):
        entities.append({
            "name": f"slime_{i + 1}",
            "type": "enemy",
            "visualDescription": f"a round green slime with big eyes, enemy #{i + 1}",
            "size": "small",
            "behaviors": [{"name": "patrol"}],
        })
    entities.append({
        "name": "exit_door",
        "type": "goal",
        "visualDescription": "a golden glowing exit door framed with runes",
        "size": "medium",
        "behaviors": [],
    })

    levels = [
        {
            "difficulty": "easy" if i == 0 else "medium",
            "length":     "medium",
            "backgroundDescription": (
                f"grassy pixel-art landscape with floating platforms, "
                f"level {i + 1} of {n_levels}"
            ),
            "goal": {"entity_name": "exit_door"},
        }
        for i in range(n_levels)
    ]

    win = VALID_WIN_CONDITION.get(archetype, "reach_door")
    return {
        "archetype":   archetype,
        "title":       f"Bench {n_enemies}e-{n_levels}L",
        "description": "Auto-generated benchmark plan",
        "style":       "pixel",
        "theme": {
            "background_color": "#1a1a2e",
            "accent_color":     "#f59e0b",
            "ground_color":     "#4a7c59",
            "hazard_color":     "#cc2200",
        },
        "parameters": {
            "max_health":           3,
            "move_speed":           220,
            "jump_velocity":        520,
            "gravity":              1400,
            "starting_lives":       3,
            "win_condition_type":   win,
            "win_condition_target": 0,
        },
        "entities": entities,
        "levels":   levels,
        "audio": {
            "soundEffects": [
                {"event": "player_jump",    "description": "jump", "durationSeconds": 0.2},
                {"event": "coin_collect",   "description": "coin", "durationSeconds": 0.3},
                {"event": "player_hit",     "description": "hurt", "durationSeconds": 0.4},
                {"event": "enemy_defeated", "description": "kill", "durationSeconds": 0.5},
                {"event": "level_complete", "description": "win",  "durationSeconds": 1.0},
            ],
            "music": {
                "description":   "upbeat chiptune adventure theme",
                "mood":          "cheerful",
                "durationSeconds": 60,
            },
        },
    }


# Plan size matrix used by bench_assets.py and bench_code.py
PLAN_SIZES = [
    {"label": "S (2e 1L)", "enemies": 2, "levels": 1},
    {"label": "M (4e 2L)", "enemies": 4, "levels": 2},
    {"label": "L (6e 3L)", "enemies": 6, "levels": 3},
    {"label": "XL(8e 3L)", "enemies": 8, "levels": 3},
]
