import streamlit as st
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig

# --- Configuration and Setup ---
load_dotenv()

st.set_page_config(page_title="Smart Task Planner", page_icon="🤖", layout="wide")

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("🚨 Missing Google API key. Please add it in your `.env` file as GOOGLE_API_KEY='your_key'.")
    st.stop()

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

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

    Provide only valid JSON — no markdown, text, or code blocks.
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # ✅ use supported model
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
            )
        )

        # Extract text safely
        ai_text = response.output_text.strip()
        ai_text = ai_text.replace("```json", "").replace("```", "").strip()

        # Parse JSON
        plan = json.loads(ai_text)
        return plan

    except json.JSONDecodeError:
        return {"error": "AI returned an invalid JSON format. Please try rephrasing your goal."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

# --- Streamlit UI ---
st.title("🎯 Smart Task Planner")
st.write("Describe your goal, and let AI break it down into a structured action plan!")

goal_input = st.text_input(
    "Enter your goal:",
    placeholder="e.g., Launch a new e-commerce mobile app in 3 months",
    key="goal_input"
)

if st.button("Generate Plan", type="primary"):
    if goal_input:
        with st.spinner("🧠 AI is crafting your plan..."):
            result = generate_plan(goal_input)

        if "error" in result:
            st.error(result["error"])
        elif "plan" in result:
            st.success("✅ Here's your action plan!")

            tasks = sorted(result["plan"], key=lambda x: x["task_id"])
            for task in tasks:
                with st.expander(f"**Task {task['task_id']}: {task['task_name']}** ({task['duration_days']} days)"):
                    st.markdown(f"**Description:** {task['description']}")
                    deps = ", ".join(map(str, task["dependencies"])) if task["dependencies"] else "None"
                    st.markdown(f"**Dependencies:** {deps}")
        else:
            st.warning("The AI didn’t generate a valid plan. Please try again.")
    else:
        st.warning("Please enter a goal first.")
