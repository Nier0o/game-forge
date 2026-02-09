import time
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from groq import Groq

# =====================================================
# CONFIG
# =====================================================

GROQ_API_KEY = "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"

THEME_MODELS = {
    "GPT-OSS-120B": "openai/gpt-oss-120b",
    "GPT-OSS-20B": "openai/gpt-oss-20b",
    "Qwen3-32B": "qwen/qwen3-32b",
    "LLaMA-3.3-70B": "llama-3.3-70b-versatile",
    "Kimi": "moonshotai/kimi-k2-instruct-0905",
    "LLaMA-4": "meta-llama/llama-4-scout-17b-16e-instruct",
}

GROQ_JUDGE_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

BASE_DIR = "theme"
LOG_DIR = f"{BASE_DIR}/logs"
os.makedirs(LOG_DIR, exist_ok=True)

client = Groq(api_key=GROQ_API_KEY)

# =====================================================
# NOISY THEME PROMPT
# =====================================================

NOISY_THEME_PROMPT = """
ok so im bad at art but i need the game to FEEL right

i dont want colorful fantasy stuff
no shiny armor
no magic glowing crystals

the world should feel old
like abandoned
stone walls
dust
rust

characters should look tired
not heroes
just someone trying to survive
simple clothes
leather maybe

items should feel useful not legendary
keys
potions
weapons that look worn out
nothing fancy

backgrounds should be dark
not pitch black
but low light
torches
shadows
fog maybe

i want pixel art
or something that could be pixel art
simple shapes
strong silhouettes

pls dont overdo it
less details but meaningful
like you can tell the story by how things look

sorry if this sounds weird
im not a designer
"""

# =====================================================
# THEME GENERATION
# =====================================================

def run_theme_model(model_id):
    start = time.time()
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "You generate visual design descriptions for games."},
            {"role": "user", "content": NOISY_THEME_PROMPT},
        ],
        temperature=0.4,
        max_tokens=800,
    )
    latency = time.time() - start
    return latency, response.choices[0].message.content

generated_outputs = {}
rows = []

for name, model_id in THEME_MODELS.items():
    print(f"Benchmarking {name}...")
    latency, output = run_theme_model(model_id)

    generated_outputs[name] = output

    with open(f"{LOG_DIR}/{name}.txt", "w", encoding="utf-8") as f:
        f.write(output)

    rows.append({
        "Model": name,
        "Latency": latency,
    })

df = pd.DataFrame(rows)

# =====================================================
# GROQ JUDGE (THEME SCORING)
# =====================================================

JUDGE_PROMPT = """
You are a professional game art director acting as a STRICT AUTOMATED EVALUATOR.

You are given:
1) A messy user description of a game's visual style
2) SIX theme design outputs

Your task:
- Evaluate EACH output independently
- Assign an INTEGER score from 1 (very poor) to 6 (excellent)
- Scores MUST be unique

Evaluate based on:
- Visual clarity
- Coverage (characters, items, environments)
- Style consistency
- Usefulness for generating game art

Rules:
- Do NOT explain your reasoning
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

def run_groq_judge(outputs: dict):
    prompt = JUDGE_PROMPT + "\n\nUSER PROMPT:\n" + NOISY_THEME_PROMPT + "\n\n"
    for name, text in outputs.items():
        prompt += f"\n--- {name} ---\n{text}\n"

    response = client.chat.completions.create(
        model=GROQ_JUDGE_MODEL,
        messages=[
            {"role": "system", "content": "You are a strict evaluator."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=300,
    )
    return response.choices[0].message.content

def extract_judge_scores(text, model_names):
    start = text.index("{")
    end = text.rindex("}") + 1
    data = json.loads(text[start:end])

    if set(data.keys()) != set(model_names):
        raise RuntimeError("Judge model names mismatch")

    if sorted(data.values()) != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("Judge scores must be unique 1–6")

    return data

judge_raw = run_groq_judge(generated_outputs)

with open(f"{BASE_DIR}/judge_output.txt", "w", encoding="utf-8") as f:
    f.write(judge_raw)

judge_scores = extract_judge_scores(judge_raw, list(THEME_MODELS.keys()))
df["Judge_Score"] = df["Model"].map(judge_scores)

# =====================================================
# NORMALIZATION & FINAL SCORE
# =====================================================

df["Latency_Norm"] = (df["Latency"].max() - df["Latency"]) / (
    df["Latency"].max() - df["Latency"].min()
)

df["Judge_Norm"] = (df["Judge_Score"] - 1) / 5

df["Final_Score"] = (
    0.85 * df["Judge_Norm"]
    + 0.15 * df["Latency_Norm"]
)

df["Final_Score_Percent"] = df["Final_Score"] * 100
df.sort_values("Final_Score_Percent", ascending=False, inplace=True)

# =====================================================
# SAVE RESULTS
# =====================================================

df.to_csv(f"{BASE_DIR}/theme_results_final.csv", index=False)
df.to_json(f"{BASE_DIR}/theme_results_final.json", orient="records", indent=2)

with open(f"{BASE_DIR}/theme_results_final.txt", "w", encoding="utf-8") as f:
    f.write(df.to_string(index=False))

# =====================================================
# GRAPH
# =====================================================

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(12, 7))

bars = ax.bar(
    df["Model"],
    df["Final_Score_Percent"],
    color=["#ff9f1c", "#2ec4b6", "#e71d36", "#9b5de5", "#f15bb5", "#00bbf9"],
    edgecolor="white",
    linewidth=1.5,
)

ax.set_title("Theme LLM Benchmark (External Judge)", fontsize=16, color="#ff9f1c")
ax.set_ylabel("Final Score (%)", fontsize=12, color="#2ec4b6")
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
plt.savefig(f"{BASE_DIR}/theme_final.jpg", dpi=300)
plt.show()
