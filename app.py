# app.py
import os
import json
import re
import ast
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()
st.set_page_config(page_title="Smart Task Planner", page_icon="🤖", layout="wide")

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("GENAI_MODEL", "gemini-2.5-flash")  # change if needed

if not API_KEY:
    st.error("🚨 GOOGLE_API_KEY not found! Add it to Streamlit Secrets or .env")
    st.stop()

# Create client (new SDK style)
client = genai.Client(api_key=API_KEY)

# -------------------------
# Helper: robust JSON parse
# -------------------------
def extract_json_from_text(text: str):
    """
    Try several approaches to extract a JSON object from the model output.
    Returns (obj, raw_used) where obj is the parsed JSON or None, raw_used is the string we attempted to parse.
    """
    if not text:
        return None, ""

    # 1) Remove common Markdown fences and codeblock markers
    cleaned = re.sub(r"(^```(?:json)?\s*|\s*```$)", "", text.strip(), flags=re.IGNORECASE)

    # 2) If the model printed explanatory lines before/after the JSON, attempt to find the first {...} .. last } block
    #    This handles cases where model adds text like "Here's the plan:" then the JSON.
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace + 1]
        try:
            return json.loads(candidate), candidate
        except json.JSONDecodeError:
            # try to "relax" python-style parsing as fallback
            try:
                return ast.literal_eval(candidate), candidate
            except Exception:
                pass

    # 3) If JSON array at top-level (starts with '[')
    first_sq = cleaned.find("[")
    last_sq = cleaned.rfind("]")
    if first_sq != -1 and last_sq != -1 and last_sq > first_sq:
        candidate = cleaned[first_sq:last_sq + 1]
        try:
            return json.loads(candidate), candidate
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(candidate), candidate
            except Exception:
                pass

    # 4) As a last attempt: try to parse the whole cleaned string
    try:
        return json.loads(cleaned), cleaned
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(cleaned), cleaned
        except Exception:
            pass

    # failed to parse
    return None, cleaned

# -------------------------
# Core: call model
# -------------------------
def generate_plan(goal: str):
    if not goal or not goal.strip():
        return {"error": "Goal cannot be empty."}

    system_prompt = (
        "You are an expert project manager AI. Output MUST be valid JSON only. "
        "Do not include any explanatory text. Only return a single JSON object."
    )

    user_prompt = f"""
The user's goal is: "{goal}"

Produce a JSON object with a single key "plan" whose value is an array of task objects.
Each task object must include:
- task_id (integer, starting at 1)
- task_name (short actionable string)
- description (short explanation)
- dependencies (array of task_id integers, empty array if none)
- duration_days (integer)

Example shape:
{{"plan":[{{"task_id":1,"task_name":"...","description":"...","dependencies":[],"duration_days":3}}, ...]}}
"""

    # We'll combine system + user prompts into a single contents string for compatibility with
    # many versions of the genai SDK. If your SDK supports messages we can change that later.
    full_prompt = system_prompt + "\n\n" + user_prompt

    try:
        # deterministic output (temperature=0) and allow more tokens
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            temperature=0.0,
            max_output_tokens=1024
        )

        # response.text is commonly where the model text is stored; fallback to str(response)
        raw = getattr(response, "text", None) or str(response)
        raw = raw.strip()

        # try to parse robustly
        parsed, used_string = extract_json_from_text(raw)

        # Show raw output in logs (Streamlit UI will display it for debugging)
        return {"raw": raw, "parsed": parsed, "used_string": used_string}

    except Exception as e:
        return {"error": f"Model call failed: {e}"}

# -------------------------
# Streamlit UI
# -------------------------
st.title("🎯 Smart Task Planner — Robust JSON Parsing")
st.write("Describe your goal and the app will ask the model to return a JSON plan. If JSON parsing fails, you'll get the raw output for debugging.")

col1, col2 = st.columns([3, 1])
with col1:
    goal_input = st.text_input(
        "Enter your goal:",
        placeholder="e.g., Launch a new e-commerce mobile app in 3 months",
        key="goal_input"
    )
    if st.button("Generate Plan"):
        with st.spinner("Calling model..."):
            result = generate_plan(goal_input)

        if "error" in result:
            st.error(result["error"])
        else:
            raw = result.get("raw", "")
            parsed = result.get("parsed")
            used = result.get("used_string", "")

            # show raw response for debugging (collapsed)
            with st.expander("📟 Raw model output (click to expand)"):
                st.code(raw)

            if parsed:
                # If parsed is a dict with plan key, show nicely
                if isinstance(parsed, dict) and "plan" in parsed:
                    st.success("✅ Parsed JSON plan successfully!")
                    tasks = parsed["plan"]
                    try:
                        tasks = sorted(tasks, key=lambda x: x["task_id"])
                    except Exception:
                        pass
                    for t in tasks:
                        with st.expander(f"Task {t.get('task_id', '?')}: {t.get('task_name', 'Unnamed')} ({t.get('duration_days','?')} days)"):
                            st.markdown(f"**Description:** {t.get('description','')}")
                            deps = t.get("dependencies", [])
                            deps_str = ", ".join(map(str, deps)) if deps else "None"
                            st.markdown(f"**Dependencies:** {deps_str}")
                else:
                    st.warning("Parsed something, but it does not contain the expected 'plan' key.")
                    st.json(parsed)
                    st.info("If parsing succeeded but the shape is wrong, check the model prompt and desired schema.")
            else:
                st.error("❌ Failed to parse valid JSON from the model output.")
                st.markdown("**What we attempted to parse (trimmed):**")
                st.code(used[:2000] + ("... (truncated)" if len(used) > 2000 else ""))
                st.markdown(
                    "Try rephrasing your goal to be shorter/simpler, or optionally click the example goal below to test a known-good prompt."
                )

with col2:
    st.markdown("### Quick actions")
    if st.button("Use example goal"):
        st.session_state["goal_input"] = "Build and launch a simple e-commerce MVP (web + mobile-responsive) in 3 months."
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("Model / settings")
    st.write(f"Model: **{MODEL}**")
    st.markdown("If parsing keeps failing, try lowering `max_output_tokens` or simplifying the goal text.")

# Footer notes
st.markdown("---")
st.markdown(
    "If you keep getting parse failures, copy the contents of the raw model output (open the 'Raw model output' panel) and paste it into a message here — I can inspect it and suggest a fix or a stricter prompt."
)
