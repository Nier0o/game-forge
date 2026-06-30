import time
import os
import pandas as pd
import matplotlib.pyplot as plt
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise SystemExit("GROQ_API_KEY environment variable is required")

client = Groq(api_key=GROQ_API_KEY)

BASE_DIR = "audio"
LOG_DIR = f"{BASE_DIR}/logs"
os.makedirs(LOG_DIR, exist_ok=True)


AUDIO_MODELS = {
    "GPT-OSS-120B": "openai/gpt-oss-120b",
    "GPT-OSS-20B": "openai/gpt-oss-20b",
    "Qwen3-32B": "qwen/qwen3-32b",
    "LLaMA-3.3-70B": "llama-3.3-70b-versatile",
    "Kimi": "moonshotai/kimi-k2-instruct-0905",
    "LLaMA-4": "meta-llama/llama-4-scout-17b-16e-instruct",
}


NOISY_AUDIO_PROMPT = """
ok i really dont know how to explain sound so pls dont expect technical stuff

i dont want epic music
no boss fight music
nothing heroic
nothing that makes me feel powerful

i want the game to feel empty
like quiet but not silent
the kind of quiet that makes you uncomfortable

i hate loud sounds
pls dont make it loud
even when its tense i want it heavy not loud

footsteps are important
sometimes stone
sometimes metal
i want to hear myself moving

enemies should not scream
i dont want jump scares
i want to hear them before i see them
breathing
dragging
chains maybe

pls no magic sounds
no spells
no lasers
no futuristic beeps or sci-fi stuff

the music should loop
i dont want to notice the loop
it should just be there

when danger is near the sound should change a little
not dramatic
just heavier

i dont know music theory
i dont know instruments
but i want the sound to make the player feel alone

also random thought but i hate tutorials so dont explain anything
just give me something i can feed into an audio generator

sorry if this doesnt make sense
"""


def score_instruction_following(text):
    score = 0

    if "epic" not in text.lower() and "heroic" not in text.lower():
        score += 1
    if "magic" not in text.lower() and "laser" not in text.lower():
        score += 1

    return score


def score_audio_coverage(text):
    score = 0
    t = text.lower()

    if "music" in t:
        score += 1
    if "ambient" in t or "atmosphere" in t or "background" in t:
        score += 1
    if "footstep" in t or "player" in t:
        score += 1
    if "enemy" in t or "breathing" in t or "chains" in t:
        score += 1

    return score


def score_generation_quality(text):
    score = 0
    t = text.lower()

    if any(k in t for k in ["slow", "low tempo", "heavy", "minimal"]):
        score += 2
    if any(k in t for k in ["reverb", "echo", "drone", "texture", "layer"]):
        score += 2
    if "loop" in t or "loopable" in t:
        score += 2

    return score



def run_model(model_id):
    start = time.time()
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "You generate audio generation prompts from messy human intent."},
            {"role": "user", "content": NOISY_AUDIO_PROMPT},
        ],
        temperature=0.4,
        max_tokens=800,
    )
    latency = time.time() - start
    return latency, response.choices[0].message.content


def benchmark_model(model_id):
    latency, output = run_model(model_id)

    instruction_score = score_instruction_following(output)
    coverage_score = score_audio_coverage(output)
    quality_score = score_generation_quality(output)

    raw_score = instruction_score + coverage_score + quality_score

    log_path = f"{LOG_DIR}/{model_id.replace('/', '_')}.txt"

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("=" * 80 + "\n")
        log.write(f"MODEL: {model_id}\n")
        log.write("-" * 80 + "\n\n")
        log.write("RAW OUTPUT:\n\n")
        log.write(output + "\n\n")
        log.write("-" * 80 + "\n")
        log.write(f"Instruction Following Score: {instruction_score}/2\n")
        log.write(f"Audio Coverage Score: {coverage_score}/4\n")
        log.write(f"Generation Quality Score: {quality_score}/6\n")
        log.write(f"RAW FINAL SCORE: {raw_score}/12\n")
        log.write(f"LATENCY: {latency:.3f} seconds\n")
        log.write("=" * 80 + "\n")

    return latency, instruction_score, coverage_score, quality_score, raw_score



rows = []

for name, model_id in AUDIO_MODELS.items():
    print(f"Benchmarking {name}...")
    latency, instr, cov, qual, raw = benchmark_model(model_id)

    rows.append({
        "Model": name,
        "Latency": latency,
        "Instruction": instr,
        "Coverage": cov,
        "Quality": qual,
        "Raw_Score": raw,
    })

df = pd.DataFrame(rows)


df["Instruction_Norm"] = df["Instruction"] / 2
df["Coverage_Norm"] = df["Coverage"] / 4
df["Quality_Norm"] = df["Quality"] / 6

df["Latency_Norm"] = (df["Latency"].max() - df["Latency"]) / (
    df["Latency"].max() - df["Latency"].min()
)

df["Final_Score_Norm"] = (
    0.50 * df["Quality_Norm"]
    + 0.25 * df["Coverage_Norm"]
    + 0.15 * df["Instruction_Norm"]
    + 0.10 * df["Latency_Norm"]
)

df["Final_Score_Percent"] = df["Final_Score_Norm"] * 100
df.sort_values("Final_Score_Percent", ascending=False, inplace=True)


df.to_csv(f"{BASE_DIR}/audio_results.csv", index=False)
df.to_json(f"{BASE_DIR}/audio_results.json", orient="records", indent=2)

with open(f"{BASE_DIR}/audio_results.txt", "w", encoding="utf-8") as f:
    f.write(df.to_string(index=False))


plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor("#05070f")
ax.set_facecolor("#05070f")

colors = ["#00ffff", "#ff00ff", "#39ff14", "#ff073a", "#faff00"]

bars = ax.bar(
    df["Model"],
    df["Final_Score_Percent"],
    color=colors[: len(df)],
    edgecolor="white",
    linewidth=1.5,
)

ax.set_title(
    "Audio LLM Benchmark",
    fontsize=16,
    fontweight="bold",
    color="#00ffff",
    pad=20,
)

ax.set_ylabel("Final Score (%)", fontsize=12, color="#39ff14")
ax.set_ylim(0, 100)
ax.tick_params(colors="white")
ax.grid(axis="y", linestyle="--", alpha=0.3)

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
        color="white",
    )

plt.tight_layout()
plt.savefig(f"{BASE_DIR}/audio_benchmark.jpg", dpi=300, facecolor=fig.get_facecolor())
plt.show()
