# save as app.py and run with: streamlit run app.py
import os
import json
from dotenv import load_dotenv
import streamlit as st

# Use the updated Google Gen AI SDK interface
# pip install google-genai
from google import genai

# --- Configuration and Setup ---
load_dotenv()

st.set_page_config(page_title="Smart Task Planner", page_icon="🤖", layout="wide")

API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    st.error("🚨 GOOGLE_API_KEY not found. Add it to a `.env` file or your environment.")
    st.stop()

# configure SDK
genai.configure(api_key=API_KEY)

# create a client for calls
client = genai.Client()

# --- Core Logic ---
def generate_plan(goal: str):
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
Provide only the raw JSON output, without any introductory text, closing text, or markdown formatting like ```json.
    """

    try:
        # Use the newer client.models.generate_content call and a supported model name.
        # gemini-2.5-flash is an example of a currently-supported text model; replace if you have access
        # to another model (e.g., gemini-2.5-pro or similar) per your quota/permissions.
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # response.text contains the model's text output in many samples
        raw = response.text.strip()

        # Remove stray Markdown fences if any
        if raw.startswith("```"):
            raw = raw.split("```", 1)[1].rsplit("```", 1)[0].strip()

        plan = json.loads(raw)
        return plan

    except json.JSONDecodeError:
        return {"error": "AI returned an invalid JSON format. Try rephrasing the goal or simplifying the request."}
    except Exception as e:
        # show a helpful error message for debugging
        return {"error": f"An unexpected error occurred: {e}"}

# --- Streamlit Frontend ---
st.title("🎯 Smart Task Planner")
st.write("Describe your goal, and let AI break it down into a manageable project plan.")

goal_input = st.text_input(
    "Enter your goal:",
    placeholder="e.g., Launch a new e-commerce mobile app in 3 months",
    key="goal_input"
)

if st.button("Generate Plan", type="primary"):
    if not goal_input:
        st.warning("Please enter a goal to get started.")
    else:
        with st.spinner("🧠 AI is crafting your plan..."):
            generated_plan = generate_plan(goal_input)

        if "error" in generated_plan:
            st.error(generated_plan["error"])
        elif "plan" in generated_plan and generated_plan["plan"]:
            st.success("✅ Here's your action plan!")
            tasks = generated_plan["plan"]
            sorted_tasks = sorted(tasks, key=lambda x: x["task_id"])
            for task in sorted_tasks:
                with st.expander(f"**Task {task['task_id']}: {task['task_name']}** ({task['duration_days']} days)"):
                    st.markdown(f"**Description:** {task['description']}")
                    dependencies = ", ".join(map(str, task["dependencies"])) if task["dependencies"] else "None"
                    st.markdown(f"**Dependencies:** This task depends on completing Task(s) **{dependencies}**.")
        else:
            st.warning("The AI couldn't generate a plan. Please try rephrasing your goal for better results.")
