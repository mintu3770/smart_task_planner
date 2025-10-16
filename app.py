# app.py
import streamlit as st
import os
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig

# -------------------------
# Configuration and Setup
# -------------------------
load_dotenv()
st.set_page_config(page_title="Smart Task Planner", page_icon="🤖", layout="wide")

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("🚨 Missing Google API key. Add it in `.env` as GOOGLE_API_KEY='your_key'")
    st.stop()

client = genai.Client(api_key=API_KEY)

# -------------------------
# Helper Functions
# -------------------------
def get_available_model():
    """Return a valid Gemini model from your API access."""
    try:
        models = client.models.list(page_size=50)
        for m in models:
            if "flash" in m.name.lower() or "pro" in m.name.lower():
                return m.name
    except Exception:
        pass

    # Fallback known stable models
    fallback_models = [
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro",
        "models/gemini-2.0-flash",
        "models/gemini-1.5-pro"
    ]
    for model in fallback_models:
        return model

    st.error("❌ No supported Gemini model found. Check API access.")
    st.stop()


def extract_json(text: str):
    """Extract the first JSON object in the text using regex."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return None

# -------------------------
# Core Function
# -------------------------
def generate_plan(goal: str):
    if not goal:
        return {"error": "Goal cannot be empty."}

    model_name = get_available_model()

    prompt = f"""
You are an expert project manager AI. Break down the user's goal into a structured action plan.
Goal: "{goal}"

⚠️ Important Instructions:
- Return **only a single valid JSON object**.
- JSON must have a key "plan" which is an array of task objects.
- Each task object must include:
    - "task_id": integer starting from 1
    - "task_name": string
    - "description": string
    - "dependencies": array of integers, empty if none
    - "duration_days": integer
- Do not include any text, markdown, or code fences.
- If you make a mistake, return **valid JSON only**.

Example:
{{"plan":[{{"task_id":1,"task_name":"...","description":"...","dependencies":[],"duration_days":3}}]}}
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0  # deterministic output
            )
        )

        ai_text = ""
        if response.candidates and response.candidates[0].content.parts:
            ai_text = response.candidates[0].content.parts[0].text.strip()

        # Extract JSON
        plan_json = extract_json(ai_text)
        if plan_json:
            return plan_json
        else:
            return {"error": "AI returned invalid JSON.", "raw": ai_text}

    except Exception as e:
        return {"error": f"Unexpected error: {e}"}

# -------------------------
# Streamlit UI
# -------------------------
st.title("🎯 Smart Task Planner")
st.write("Describe your goal, and AI will generate a structured action plan!")

goal_input = st.text_input(
    "Enter your goal:",
    placeholder="e.g., Launch a minimal e-commerce web app in 4 weeks",
    key="goal_input"
)

if st.button("Generate Plan", type="primary"):
    if goal_input:
        with st.spinner("🧠 AI is generating your plan..."):
            result = generate_plan(goal_input)

        if "error" in result:
            st.error(result["error"])
            if "raw" in result:
                with st.expander("📟 Raw AI output"):
                    st.code(result["raw"])
        elif "plan" in result:
            st.success("✅ AI-generated action plan:")

            tasks = sorted(result["plan"], key=lambda x: x.get("task_id", 0))
            for task in tasks:
                with st.expander(f"Task {task.get('task_id', '?')}: {task.get('task_name', 'Unnamed')} ({task.get('duration_days', '?')} days)"):
                    st.markdown(f"**Description:** {task.get('description', '')}")
                    deps = ", ".join(map(str, task.get("dependencies", []))) if task.get("dependencies") else "None"
                    st.markdown(f"**Dependencies:** {deps}")
        else:
            st.warning("AI did not return a valid plan. Try rephrasing your goal.")
    else:
        st.warning("Please enter a goal first.")
