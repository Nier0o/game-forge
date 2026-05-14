import time
import os
import pandas as pd
import json
import matplotlib.pyplot as plt
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise SystemExit("GROQ_API_KEY environment variable is required")

client = Groq(api_key=GROQ_API_KEY)
BASE_DIR = "coder"
LOG_DIR = f"{BASE_DIR}/logs"
os.makedirs(LOG_DIR, exist_ok=True)
GROQ_JUDGE_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

# =====================================================
# CODER MODELS
# =====================================================

CODER_MODELS = {
    "GPT-OSS-120B": "openai/gpt-oss-120b",
    "GPT-OSS-20B": "openai/gpt-oss-20b",
    "Qwen3-32B": "qwen/qwen3-32b",
    "LLaMA-3.3-70B": "llama-3.3-70b-versatile",
    "Kimi": "moonshotai/kimi-k2-instruct-0905",
    "LLaMA-4": "meta-llama/llama-4-scout-17b-16e-instruct",
}

# =====================================================
# NOISY HUMAN PROMPT
# =====================================================

NOISY_CODE_PROMPT = """
ok so im kinda lost here but i need help

im trying to make a very small 2d game
nothing fancy
just logic

i want a player that moves around
and can hit stuff with a sword
no guns
no magic
pls dont add spells later

enemies exist
they should kinda follow the player
if they get close they attack
idk how to do ai properly so keep it simple

i dont want big architecture
no huge classes
no engine stuff
just python logic
like a game loop
update functions maybe

idk if state machines are needed
but if u use them keep it simple
idle
move
attack
something like that

i hate overengineering
pls dont make it confusing
i want to be able to change things later

also dont worry about graphics
just logic
movement
distance checks
cooldowns maybe

language is python
pretend this runs inside a simple loop
not pygame
not unity
not unreal

sorry if this is messy
im bad at explaining
"""

# =====================================================
# STATIC SCORING
# =====================================================


def score_instruction(text):
    return int("magic" not in text.lower() and "gun" not in text.lower()) + int(
        "def " in text
    )


def score_structure(text):
    return sum(k in text.lower() for k in ["player", "enemy", "update", "attack"])


def score_behavior(text):
    return sum(k in text.lower() for k in ["move", "distance", "cooldown", "state"])


def score_soundness(text):
    return int("def " in text) + int(len(text.splitlines()) > 15)


# =====================================================
# GROQ CODE GENERATION
# =====================================================


def run_coder_model(model_id):
    start = time.time()
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": "Generate simple, readable Python game logic.",
            },
            {"role": "user", "content": NOISY_CODE_PROMPT},
        ],
        temperature=0.2,
        max_tokens=1000,
    )
    latency = time.time() - start
    return latency, response.choices[0].message.content


generated_codes = {}
rows = []

for name, model_id in CODER_MODELS.items():
    print(f"Benchmarking {name}...")
    latency, code = run_coder_model(model_id)

    generated_codes[name] = code

    with open(f"{LOG_DIR}/{name}.txt", "w", encoding="utf-8") as f:
        f.write(code)

    rows.append(
        {
            "Model": name,
            "Latency": latency,
            "Instruction": score_instruction(code),
            "Structure": score_structure(code),
            "Behavior": score_behavior(code),
            "Soundness": score_soundness(code),
        }
    )

df = pd.DataFrame(rows)

# =====================================================
# GROQ JUDGE (NUMERIC SCORING 1–6)
# =====================================================

JUDGE_PROMPT = """
You are an expert Python game developer acting as a STRICT AUTOMATED EVALUATOR.

You are given:
1) A messy user request for a small 2D game
2) SIX Python code solutions

Your task:
- Evaluate EACH solution independently
- Assign an INTEGER score from 1 (very poor) to 6 (excellent)
- Scores MUST be unique (no ties)

Scoring criteria:
- Correctness of game logic
- Completeness relative to the request
- Clarity and simplicity
- No extra or forbidden features

Rules:
- Do NOT explain your reasoning
- Do NOT rewrite code
- Do NOT add text outside JSON
- Output ONLY valid JSON
- Use EXACT model names as keys

Output format:
{
  "GPT-OSS-120B": 6,
  "GPT-OSS-20B": 5,
  "Qwen3-32B": 4,
  "LLaMA-3.3-70B": 3,
  "Kimi": 2,
  "LLaMA-4": 1
}
"""


def run_groq_judge(codes: dict):
    prompt = JUDGE_PROMPT + "\n\nUSER REQUEST:\n" + NOISY_CODE_PROMPT + "\n\n"
    for name, code in codes.items():
        prompt += f"\n--- {name} ---\n{code}\n"

    response = client.chat.completions.create(
        model=GROQ_JUDGE_MODEL,
        messages=[
            {"role": "system", "content": "You are a strict evaluator."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=400,
    )
    return response.choices[0].message.content


def extract_judge_scores(text, model_names):
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
    except Exception:
        raise RuntimeError("Judge did not return valid JSON:\n" + text)

    if set(data.keys()) != set(model_names):
        raise RuntimeError("Judge output model mismatch")

    scores = list(data.values())
    if sorted(scores) != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("Judge scores must be unique 1–6")

    return data


judge_raw = run_groq_judge(generated_codes)

with open(f"{BASE_DIR}/judge_output.txt", "w", encoding="utf-8") as f:
    f.write(judge_raw)

judge_scores = extract_judge_scores(judge_raw, list(CODER_MODELS.keys()))
df["Judge_Score"] = df["Model"].map(judge_scores)

# =====================================================
# NORMALIZATION
# =====================================================

df["Instruction_Norm"] = df["Instruction"] / 2
df["Structure_Norm"] = df["Structure"] / 4
df["Behavior_Norm"] = df["Behavior"] / 4
df["Soundness_Norm"] = df["Soundness"] / 2

df["Latency_Norm"] = (df["Latency"].max() - df["Latency"]) / (
    df["Latency"].max() - df["Latency"].min()
)

df["Judge_Norm"] = (df["Judge_Score"] - 1) / 5

# =====================================================
# FINAL SCORE (JUDGE DOMINANT)
# =====================================================

df["Final_Score"] = (
    0.40 * df["Judge_Norm"]
    + 0.25 * df["Behavior_Norm"]
    + 0.15 * df["Structure_Norm"]
    + 0.10 * df["Instruction_Norm"]
    + 0.05 * df["Soundness_Norm"]
    + 0.05 * df["Latency_Norm"]
)

df["Final_Score_Percent"] = df["Final_Score"] * 100
df.sort_values("Final_Score_Percent", ascending=False, inplace=True)

# =====================================================
# SAVE RESULTS
# =====================================================

df.to_csv(f"{BASE_DIR}/coder_results_final.csv", index=False)
df.to_json(f"{BASE_DIR}/coder_results_final.json", orient="records", indent=2)

with open(f"{BASE_DIR}/coder_results_final.txt", "w", encoding="utf-8") as f:
    f.write(df.to_string(index=False))

# =====================================================
# GRAPH
# =====================================================

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(12, 7))

colors = ["#00ffff", "#ff00ff", "#39ff14", "#ff073a", "#faff00", "#8a2be2"]

bars = ax.bar(
    df["Model"],
    df["Final_Score_Percent"],
    color=colors,
    edgecolor="white",
    linewidth=1.5,
)

ax.set_title(
    "Coder LLM Benchmark (External Groq Judge)",
    fontsize=16,
    fontweight="bold",
    color="#00ffff",
    pad=20,
)

ax.set_ylabel("Final Score (%)", fontsize=12, color="#39ff14")
ax.set_ylim(0, 100)
ax.grid(axis="y", linestyle="--", alpha=0.3)

for bar in bars:
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        h + 1.5,
        f"{h:.1f}%",
        ha="center",
        color="white",
        fontweight="bold",
    )

plt.tight_layout()
plt.savefig(f"{BASE_DIR}/coder_final_neon.jpg", dpi=300)
plt.show()
