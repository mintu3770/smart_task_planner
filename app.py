import os
import json
import streamlit as st
from dotenv import load_dotenv

# ✅ NEW official Google SDK (make sure you install it via: pip install google-genai)
from google import genai

# -------------------------------
# 🔧 Configuration and Setup
# -------------------------------
load_dotenv()

st.set_page_config(page_title="Smart Task Planner", page_icon="🤖", layout="wide")

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("🚨 GOOGLE_API_KEY not found! Please set it in your environment variables or Streamlit Secrets.")
    st.stop()

# Configure GenAI client
genai.configure(api_key=API_KEY)
client = genai.Client()

# -------------------------------
# 🧠 Core Logic
# -------------------------------
def generate_plan(goal: str):
    """Generate a structured project plan based on a user goal."""
    if not goal:
        return {"error": "Goal cannot be empty."}

    prompt = f"""
You are an expert project manager AI. Your task is to break down a complex user goal into a detailed, actionable plan.
The user's goal is: "{goal}"

Please generate a plan as a structured JSON object. The JSON object must have a single key "plan" which is an array of task objects.
Each task object must have the following keys:
- "task_id": A unique integer identifier for the task, starting from 1.
- "task_name": A concise, actionable name for the task.
- "description": A brief explanation of what the task involves and why it's important.
- "dependencies": An array of `task_id`s that this task depends on. An empty array [] means it has no dependencies.
- "duration_days": An estimated integer for the number of days required to complete the task.

Analyze the goal carefully and create a logical sequence of tasks. Ensure that dependencies are correctly identified.
Provide only the raw JSON output, without any introductory text or markdown formatting.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # ✅ Supported model name
            contents=prompt
        )

        raw = response.text.strip()
        # Clean any markdown fences
        if raw.startswith("```"):
            raw = raw.split("```", 1)[1].rsplit("```", 1)[0].strip()

        plan = json.loads(raw)
        return plan

    except json.JSONDecodeError:
        return {"error": "AI returned an invalid JSON format. Please try rephrasing your goal."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

# -------------------------------
# 🎨 Streamlit UI
# -------------------------------
st.title("🎯 Smart Task Planner")
st.write("Describe your goal, and let AI break it down into a detailed, actionable project plan.")

goal_input = st.text_input(
    "Enter your goal:",
    placeholder="e.g., Launch a new e-commerce mobile app in 3 months",
    key="goal_input"
)

if st.button("Generate Plan", type="primary"):
    if not goal_input.strip():
        st.warning("Please enter a goal to get started.")
    else:
        with st.spinner("🧠 AI is crafting your plan..."):
            result = generate_plan(goal_input)

        if "error" in result:
            st.error(result["error"])
        elif "plan" in result and result["plan"]:
            st.success("✅ Here's your AI-generated action plan!")

            tasks = sorted(result["plan"], key=lambda x: x["task_id"])

            for task in tasks:
                with st.expander(f"**Task {task['task_id']}: {task['task_name']}** ({task['duration_days']} days)"):
                    st.markdown(f"**Description:** {task['description']}")
                    deps = ", ".join(map(str, task["dependencies"])) if task["dependencies"] else "None"
                    st.markdown(f"**Dependencies:** {deps}")
        else:
            st.warning("⚠️ AI could not generate a plan. Try refining your goal description.")
