"""AI causal narrative layer — DEMO PATH ONLY.

⚠ HARD RULE: this module makes network calls and must NEVER be imported by
run.sh, src/generate_features.py, src/predict.py or src/train.py. The grading
pipeline forbids network access at run time. It is imported only by app.py
and notebooks.

Provider chain (each failure falls through, generate_narrative NEVER raises):

    Gemini (GEMINI_API_KEY)  ->  Hugging Face (HF_TOKEN)  ->  rule-based template

Keys come from environment variables only — never hardcoded, never committed.
With zero keys set, the template still produces a coherent analyst summary,
so the demo cannot crash mid-presentation.
"""

import json
import os

_ENV_LOADED = False


def _load_env_file() -> None:
    """Load key=value pairs from a project-root .env into os.environ (once).

    Existing environment variables always win, so a real shell export is never
    clobbered by the file. Uses python-dotenv when available, otherwise a
    minimal built-in parser so the .env still works with zero extra installs.
    """
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root, ".env")
    if not os.path.exists(env_path):
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=False)
        return
    except Exception:  # noqa: BLE001 — dotenv missing; fall back to manual parse
        pass

    try:
        with open(env_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                name = name.strip()
                value = value.strip().strip('"').strip("'")
                if name and name not in os.environ:
                    os.environ[name] = value
    except Exception as e:  # noqa: BLE001
        print(f"[narrative] could not read .env ({type(e).__name__}: {e})")


PERSONA = (
    "You are a senior performance marketing analyst at a top-tier digital "
    "agency. You write executive summaries that account directors present "
    "directly to e-commerce clients."
)

# Override with GEMINI_MODEL in the environment / .env if your key's project
# has quota for a different model. The 2.0-flash free tier is limit:0 on some
# projects; 2.5-flash is broadly available.
GEMINI_MODEL = "gemini-2.5-flash"
# Ungated instruction-tuned model — Llama models require a license click-through
# that can silently fail.
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"


# ---------------------------------------------------------------------------
# Context assembly
# ---------------------------------------------------------------------------

def build_context(forecast_total: dict, trailing: dict, channels: list,
                  anomalies: list, regime_shifts: list, optimizer: dict,
                  calibration: dict, seasonality_note: str = "") -> dict:
    """Structured context object. Feeding the LLM structure + evidence (not a
    bare table) is what produces reasoning instead of paraphrase.
    """
    return {
        "forecast_30d": forecast_total,          # P10/P50/P90 revenue + blended ROAS
        "actual_trailing_30d": trailing,         # reality anchor
        "channels": channels,                    # spend/revenue/roas/top campaign types
        "detected_anomalies": anomalies,
        "regime_shifts": regime_shifts,          # e.g. a channel's ROAS collapse
        "optimizer_verdict": optimizer,
        "calibration": calibration,              # empirical band coverage
        "seasonality": seasonality_note,
    }


def build_prompt(ctx: dict) -> str:
    return f"""{PERSONA}

Below is the structured output of a probabilistic revenue forecasting system
for an e-commerce client's paid media program (Google, Meta, Microsoft).

DATA (JSON):
{json.dumps(ctx, indent=2, default=str)}

Write an executive summary that:
1. Explains WHY revenue is expected to move the way it is — reason causally
   about channel mix, seasonality and efficiency; do not merely restate numbers.
2. Identifies WHICH channel carries the most risk and explains the MECHANISM
   behind that risk, citing the detected anomalies as evidence.
3. Gives ONE specific, actionable recommendation for this week.
4. Explains how the client should interpret the P10-P90 uncertainty band,
   referencing the empirical calibration.
5. Uses agency vocabulary naturally: blended ROAS, channel contribution,
   media efficiency, budget pacing, incrementality.
6. Is specific with numbers and avoids hedging ("may", "could") where the
   data is clear.

Format: exactly 3 paragraphs of flowing prose. No headings, no bullet points.
It should read like a summary an account director hands a client."""


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

def _gemini(prompt: str, key: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=key)
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", GEMINI_MODEL))
    resp = model.generate_content(prompt)
    text = (resp.text or "").strip()
    if not text:
        raise ValueError("Gemini returned an empty response")
    return text


def _huggingface(prompt: str, token: str, model: str = HF_MODEL) -> str:
    import requests
    resp = requests.post(
        f"https://api-inference.huggingface.co/models/{model}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "inputs": f"<s>[INST] {prompt} [/INST]",
            "parameters": {"max_new_tokens": 700, "temperature": 0.4,
                           "return_full_text": False},
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data[0]["generated_text"].strip() if isinstance(data, list) else ""
    if not text:
        raise ValueError("Hugging Face returned an empty response")
    return text


def _template(ctx: dict) -> str:
    """Rule-based fallback: zero network, zero dependencies, never fails."""
    f = ctx.get("forecast_30d", {})
    t = ctx.get("actual_trailing_30d", {})
    shifts = ctx.get("regime_shifts", [])
    opt = ctx.get("optimizer_verdict", {})
    cal = ctx.get("calibration", {})
    channels = ctx.get("channels", [])

    top = max(channels, key=lambda c: c.get("revenue", 0), default={})
    coverage = cal.get("coverage_pct", cal.get("inside", ""))

    para1 = (
        f"Over the next 30 days we project revenue of ${f.get('revenue_p50', 0):,.0f} "
        f"(P50) on planned spend of ${f.get('spend', 0):,.0f}, a blended ROAS of "
        f"{f.get('roas_p50', 0):.2f}x, against ${t.get('revenue', 0):,.0f} delivered in the "
        f"trailing 30 days at {t.get('roas', 0):.2f}x. "
        f"{top.get('channel', 'The lead channel').title()} remains the primary revenue "
        f"engine and its channel contribution is driven by its highest-share campaign "
        f"types; media efficiency at the current budget pacing is consistent with the "
        f"recent trend, and the forecast assumes spend continues at that pacing."
    )

    if shifts:
        s = shifts[0]
        para2 = (
            f"The clearest risk sits with {s.get('channel', 'a minor channel')}: its blended "
            f"ROAS has moved from {s.get('historical_roas', 0):.2f}x historically to "
            f"{s.get('recent_roas', 0):.2f}x in recent weeks ({s.get('change_pct', 0):+.0f}%), a "
            f"regime shift flagged automatically by our anomaly monitor rather than a "
            f"one-week blip. Until the driver is diagnosed (tracking, auction pressure, or "
            f"creative fatigue), incremental dollars there buy less revenue than the same "
            f"dollars in stronger channels. "
        )
    else:
        para2 = ("No channel-level efficiency regime shift was detected this period; "
                 "risk is concentrated in normal week-to-week volatility. ")
    para2 += (
        f"Our allocation optimizer, constrained to stay within historically observed "
        f"spend ranges, finds the current mix close to optimal "
        f"(maximum available lift {opt.get('lift_pct', 0):+.1f}%) — the recommended action is "
        f"{opt.get('action', 'to hold the current allocation and monitor')}"
    )

    para3 = (
        f"Read the forecast as a range, not a point: P10 ${f.get('revenue_p10', 0):,.0f} to "
        f"P90 ${f.get('revenue_p90', 0):,.0f}. The band is conformally calibrated — "
        f"{coverage or 'approximately 80%'} of historical outcomes landed inside it — so "
        f"outcomes near P10 signal a genuine underperformance to act on, not model noise. "
        f"Plan inventory and cash against P50, stress-test against P10, and treat P90 as "
        f"upside if seasonality breaks favourably."
    )
    return "\n\n".join([para1, para2, para3])


# ---------------------------------------------------------------------------
# Public entry point — never raises
# ---------------------------------------------------------------------------

def generate_narrative(ctx: dict) -> tuple[str, str]:
    """Returns (narrative_text, provider_used). Tries Gemini -> HF -> template."""
    _load_env_file()
    prompt = build_prompt(ctx)

    key = os.environ.get("GEMINI_API_KEY")
    if key:
        try:
            return _gemini(prompt, key), "gemini"
        except Exception as e:  # noqa: BLE001 — graceful degradation by design
            print(f"[narrative] Gemini failed ({type(e).__name__}: {e}) — falling back")
    else:
        print("[narrative] GEMINI_API_KEY not set — skipping Gemini")

    token = os.environ.get("HF_TOKEN")
    if token:
        try:
            return _huggingface(prompt, token), "huggingface"
        except Exception as e:  # noqa: BLE001
            print(f"[narrative] Hugging Face failed ({type(e).__name__}: {e}) — falling back")
    else:
        print("[narrative] HF_TOKEN not set — skipping Hugging Face")

    return _template(ctx), "template"
