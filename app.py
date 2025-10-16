# app.py
import streamlit as st
import os
import json
from dotenv import load_dotenv
# Corrected: Use the standard import for the library
import google.generativeai as genai

# -------------------------
# Configuration and Setup
# -------------------------
load_dotenv()
st.set_page_config(page_title="Smart Task Planner", page_icon="🎯", layout="wide")

# Use a try-except block for safer key retrieval
try:
    API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.error("🚨 Missing Google API key. Add it to your environment as GOOGLE_API_KEY.")
    st.stop()
except Exception as e:
    st.error(f"🚨 An error occurred during API configuration: {e}")
    st.stop()


# -------------------------
# Helper Function (Simplified)
# -------------------------
def get_model():
    """Returns a configured GenerativeModel instance."""
    # Using gemini-1.5-flash is a good, fast choice.
    return genai.GenerativeModel("gemini-1.5-flash")

# -------------------------
# Core Function
# -------------------------
def generate_plan(goal: str):
    if not goal:
        return {"error": "Goal cannot be empty."}

    prompt = f"""
You are an expert project manager AI. Your task is to break down the user's goal into a structured action plan.
Goal: "{goal}"

Return a single, valid JSON object with a key "plan". The "plan" key should hold an array of task objects.
Each task object must include:
  - "task_id": (integer) A unique ID for the task, starting from 1.
  - "task_name": (string) A concise name for the task.
  - "description": (string) A detailed description of what the task involves.
  - "dependencies": (array of integers) A list of 'task_id's that must be completed before this task can start. Use an empty array [] if there are no dependencies.
  - "duration_days": (integer) The estimated number of days to complete the task.
"""
    
    try:
        model = get_model()

        # Configure the generation settings to enforce JSON output
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.3,
            max_output_tokens=4096,
        )

        response = model.generate_content(
            contents=prompt,
            generation_config=generation_config
        )

        # Directly parse the JSON response text
        try:
            plan_json = json.loads(response.text)
            # Basic validation to ensure the structure is correct
            if "plan" in plan_json and isinstance(plan_json["plan"], list):
                return plan_json
            else:
                 return {"error": "AI returned JSON in an unexpected format.", "raw": response.text}
        except json.JSONDecodeError:
            return {"error": "AI failed to return a valid JSON object.", "raw": response.text}
        except Exception as e:
            return {"error": f"Error parsing AI response: {e}", "raw": response.text}

    except Exception as e:
        # Catch potential API errors (e.g., authentication, quota)
        return {"error": f"An error occurred while calling the AI model: {e}"}

# -------------------------
# Streamlit UI
# -------------------------
st.title("🎯 Smart Task Planner")
st.write("Describe your goal, and AI will generate a structured action plan!")

if "goal_input" not in st.session_state:
    st.session_state.goal_input = "Build a minimal e-commerce web app in 4 weeks."

goal_input = st.text_input(
    "Enter your goal:",
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
            tasks = result.get("plan", [])
            if not tasks:
                 st.warning("The AI generated an empty plan. Try a more specific goal.")
                 return

            st.success("✅ Here is your AI-generated action plan:")
            
            # Sort tasks by ID for a logical display order
            sorted_tasks = sorted(tasks, key=lambda x: x.get("task_id", 0))
            
            for task in sorted_tasks:
                task_id = task.get('task_id', '?')
                task_name = task.get('task_name', 'Unnamed Task')
                duration = task.get('duration_days', '?')

                with st.expander(f"**Task {task_id}: {task_name}** ({duration} days)"):
                    st.markdown(f"**Description:** {task.get('description', 'No description provided.')}")
                    dependencies = task.get("dependencies", [])
                    deps_str = ", ".join(map(str, dependencies)) if dependencies else "None"
                    st.markdown(f"**Dependencies:** Task(s) {deps_str}")
        else:
            st.warning("The AI did not return a valid plan. Please try rephrasing your goal.")
    else:
        st.warning("Please enter a goal first.")
