# app.py
import streamlit as st
import os
import json
# The `re` module is no longer needed
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig

# -------------------------
# Configuration and Setup
# -------------------------
load_dotenv()
st.set_page_config(page_title="Smart Task Planner", page_icon="🎯", layout="wide")

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("🚨 Missing Google API key. Add it in `.env` as GOOGLE_API_KEY='your_key'")
    st.stop()

# Initialize the client
# Note: Using genai.configure(api_key=API_KEY) is the more common pattern
genai.configure(api_key=API_KEY)

# -------------------------
# Helper Functions
# -------------------------
def get_available_model():
    """Return a valid Gemini model."""
    # This function can be simplified as the model names are standard
    return "models/gemini-1.5-flash"


# The extract_json function is no longer needed.

# -------------------------
# Core Function
# -------------------------
def generate_plan(goal: str):
    if not goal:
        return {"error": "Goal cannot be empty."}

    # Simplified the prompt as instructions are now handled by the API config
    prompt = f"""
You are an expert project manager AI. Break down the user's goal into a structured action plan.
Goal: "{goal}"

Return a JSON object with a key "plan" which is an array of task objects.
Each task object must include:
  - "task_id": integer starting from 1
  - "task_name": string
  - "description": string
  - "dependencies": array of integers, empty if none
  - "duration_days": integer
"""
    
    try:
        model = genai.GenerativeModel(get_available_model())

        # Correctly configure the generation settings
        generation_config = GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=2048,
        )

        response = model.generate_content(
            contents=prompt,
            generation_config=generation_config
        )

        ai_text = response.text.strip()

        # Directly parse the JSON since the output is guaranteed to be a JSON string
        try:
            plan_json = json.loads(ai_text)
            # Basic validation
            if "plan" in plan_json and isinstance(plan_json["plan"], list):
                return plan_json
            else:
                 return {"error": "AI returned JSON in the wrong format.", "raw": ai_text}
        except json.JSONDecodeError:
            return {"error": "AI failed to return a valid JSON object.", "raw": ai_text}

    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

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
            st.error(f'**Error:** {result["error"]}')
            if "raw" in result and result["raw"]:
                with st.expander("📟 Raw AI output"):
                    st.code(result["raw"], language="text")
        elif "plan" in result:
            st.success("✅ AI-generated action plan:")
            
            # Sort tasks by ID for correct display order
            tasks = sorted(result["plan"], key=lambda x: x.get("task_id", 0))

            if not tasks:
                 st.warning("The generated plan is empty. Try a more specific goal.")
            
            for task in tasks:
                with st.expander(f"**Task {task.get('task_id', '?')}: {task.get('task_name', 'Unnamed')}** ({task.get('duration_days', '?')} days)"):
                    st.markdown(f"**Description:** {task.get('description', 'No description provided.')}")
                    deps = ", ".join(map(str, task.get("dependencies", []))) if task.get("dependencies") else "None"
                    st.markdown(f"**Dependencies:** Task(s) {deps}")
        else:
            st.warning("AI did not return a valid plan. Try rephrasing your goal.")
    else:
        st.warning("Please enter a goal first.")
