import time
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import jsonschema
from groq import Groq

# =====================================================
# GROQ CLIENT
# =====================================================

client = Groq(api_key="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")

BASE_DIR = "planner"
LOG_DIR = f"{BASE_DIR}/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# =====================================================
# PLANNER MODELS
# =====================================================

PLANNER_MODELS = {
    "GPT-OSS-120B": "openai/gpt-oss-120b",
    "GPT-OSS-20B": "openai/gpt-oss-20b",
    "Qwen3-32B": "qwen/qwen3-32b",
    "LLaMA-3.3-70B": "llama-3.3-70b-versatile",
    "Kimi": "moonshotai/kimi-k2-instruct-0905",
    "LLaMA-4": "meta-llama/llama-4-scout-17b-16e-instruct",
}

# =====================================================
# PROMPT
# =====================================================

NOISY_PROMPT = """
ok this might sound dumb but hear me out pls

so i kinda want to make a game or maybe its more like a vibe idk
i was thinking about those old games i used to play when the electricity cuts
and u just sit in the dark and imagine stuff

first thing: pls no guns. i really dont like guns in games.
also magic is kinda boring so lets skip spells and lasers and fireballs
i guess swords r fine tho like a normal sword nothing fancy

idk if this matters but my laptop is old and loud so pls dont make it huge
like not open world not multiple maps
one map is more than enough honestly
if u put more than one level its probably too much

the game should feel dark, not horror jumpscare dark but like quiet dark
u know when the music is low and footsteps echo
maybe enemies exist but they arent screaming all the time

also idk why but pixel art feels right for this
maybe because i like old games
but dont focus too much on graphics this is about gameplay

the player should walk around and explore
maybe avoid some enemies or fight them
but close combat only
pls dont suddenly add bows or guns later

goal?? hmm
maybe survive?
or escape?
or reach something like an exit door or stairs
basically there should be a clear way to win not just endless fighting

random thought: i watched a movie yesterday ignore that
also i hate tutorials so dont make it complicated

pls keep it simple but meaningful
dont add features just because u can
less is more

ok hope that made sense lol
"""

# =====================================================
# SCHEMA
# =====================================================

SCHEMA = {
    "type": "object",
    "required": ["genre", "player", "level", "win_condition", "theme"],
    "properties": {
        "genre": {"type": "string"},
        "player": {"type": "string"},
        "level": {"type": "string"},
        "win_condition": {"type": "string"},
        "theme": {"type": "string"},
    },
}

# =====================================================
# PROMPT BUILDER
# =====================================================


def build_prompt():
    return f"""
You are a professional game planner.

The user message below is extremely noisy, informal, and unstructured.
Your task is to REASON about it and extract the intended game idea.

Rules:
- Output ONLY valid JSON
- Follow the JSON schema STRICTLY
- Ignore irrelevant or contradictory information
- Resolve ambiguity reasonably
- Do NOT hallucinate features
- Do NOT add mechanics the user did not imply

User Message:
{NOISY_PROMPT}

JSON Schema:
{json.dumps(SCHEMA)}
"""


# =====================================================
# HELPERS
# =====================================================


def extract_json(text):
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except:
        return None


def is_pure_json(text):
    try:
        json.loads(text)
        return True
    except:
        return False


def safe_filename(name):
    return name.replace("/", "_").replace(" ", "_")


def score_reasoning(data):
    score = 0
    if any(
        k in data.get("genre", "").lower()
        for k in ["top-down", "dungeon", "exploration"]
    ):
        score += 2
    if "sword" in data.get("player", "").lower() and not any(
        w in data.get("player", "").lower() for w in ["gun", "magic", "bow"]
    ):
        score += 2
    if any(k in data.get("level", "").lower() for k in ["one", "single", "only"]):
        score += 1
    if any(
        k in data.get("win_condition", "").lower()
        for k in ["escape", "exit", "reach", "survive"]
    ):
        score += 1
    if any(
        k in data.get("theme", "").lower()
        for k in ["dark", "quiet", "mysterious", "tense"]
    ):
        score += 2
    return score


# =====================================================
# MODEL EXECUTION
# =====================================================


def run_model(model_id):
    start = time.time()
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "You extract intent from messy human input."},
            {"role": "user", "content": build_prompt()},
        ],
        temperature=0.3,
        max_tokens=600,
    )
    latency = time.time() - start
    return latency, response.choices[0].message.content


def benchmark_model(model_id):
    latency, output = run_model(model_id)

    score = 0
    breakdown = {
        "pure_json": 0,
        "schema": 0,  
        "reasoning": 0, 
    }

    log_path = f"{LOG_DIR}/{safe_filename(model_id)}.txt"

    with open(log_path, "w", encoding="utf-8") as log:

        def log_print(t=""):
            log.write(t + "\n")

        log_print("=" * 80)
        log_print(f"MODEL: {model_id}")
        log_print("RAW OUTPUT:")
        log_print(output)
        log_print("-" * 80)

        if is_pure_json(output):
            data = json.loads(output)
            breakdown["pure_json"] = 2
            score += 2
            log_print("PURE JSON (+2)")
        else:
            data = extract_json(output)
            if data is not None:
                breakdown["pure_json"] = 1
                score += 1
                log_print("RECOVERABLE JSON (+1)")
            else:
                breakdown["pure_json"] = 0
                score -= 1
                log_print("NO JSON (-1)")

        if data is not None:
            log_print("\nEXTRACTED JSON:")
            log_print(json.dumps(data, indent=2))

            try:
                jsonschema.validate(data, SCHEMA)
                breakdown["schema"] = 2
                score += 2
                log_print("SCHEMA PASS (+2)")
            except Exception as e:
                log_print(f"SCHEMA FAIL: {e}")

            r = score_reasoning(data)
            breakdown["reasoning"] = r
            score += r
            log_print(f"REASONING SCORE: {r}")

        log_print(f"\nFINAL RAW SCORE: {score}")
        log_print(f"LATENCY: {latency:.3f}s")
        log_print("=" * 80)

    return latency, score, breakdown


# =====================================================
# RUN BENCHMARK
# =====================================================

rows = []

for name, model_id in PLANNER_MODELS.items():
    print(f"Running {name}...")
    latency, raw_score, breakdown = benchmark_model(model_id)
    rows.append(
        {
            "Model": name,
            "Latency": latency,
            "Raw_Final_Score": raw_score,
            "Pure_JSON_Score": breakdown["pure_json"],
            "Schema_Score": breakdown["schema"],
            "Reasoning_Score": breakdown["reasoning"],
        }
    )

df = pd.DataFrame(rows)

# =====================================================
# NORMALIZATION
# =====================================================

df["Pure_JSON_Norm"] = df["Pure_JSON_Score"] / 2
df["Schema_Norm"] = df["Schema_Score"] / 2
df["Reasoning_Norm"] = df["Reasoning_Score"] / 8

df["Latency_Norm"] = (df["Latency"].max() - df["Latency"]) / (
    df["Latency"].max() - df["Latency"].min()
)

df["Final_Score_Norm"] = (
    0.55 * df["Reasoning_Norm"]
    + 0.20 * df["Schema_Norm"]
    + 0.15 * df["Pure_JSON_Norm"]
    + 0.10 * df["Latency_Norm"]
)

df["Final_Score_Percent"] = df["Final_Score_Norm"] * 100
df.sort_values("Final_Score_Percent", ascending=False, inplace=True)

# =====================================================
# SAVE RESULTS
# =====================================================

df.to_csv(f"{BASE_DIR}/planner_results.csv", index=False)
df.to_json(f"{BASE_DIR}/planner_results.json", orient="records", indent=2)

with open(f"{BASE_DIR}/planner_results.txt", "w", encoding="utf-8") as f:
    f.write(df.to_string(index=False))

# =====================================================
# GRAPH (PERCENTAGE)
# =====================================================

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor("#0b0f1a")
ax.set_facecolor("#0b0f1a")

colors = ["#00ffff", "#ff00ff", "#39ff14", "#ff073a", "#faff00", "#8a2be2"]

bars = ax.bar(
    df["Model"],
    df["Final_Score_Percent"],
    color=colors[: len(df)],
    edgecolor="#ffffff",
    linewidth=1.5,
)

ax.set_title(
    "Planner LLM Benchmark",
    fontsize=16,
    fontweight="bold",
    color="#00ffff",
    pad=20,
)

ax.set_ylabel("Final Score (%)", fontsize=12, color="#39ff14")
ax.set_ylim(0, 100)

ax.tick_params(colors="#ffffff")
ax.grid(axis="y", linestyle="--", alpha=0.3, color="#888888")

for bar in bars:
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        h + 1.5,
        f"{h:.1f}%",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        color="#ffffff",
    )

plt.tight_layout()
plt.savefig(
    f"{BASE_DIR}/planner_benchmark.jpg", dpi=300, facecolor=fig.get_facecolor()
)
plt.show()
