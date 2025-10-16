import streamlit as st
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# --- Configuration and Setup ---

# Load environment variables from .env file
load_dotenv()

# Set up page configuration for a better layout
st.set_page_config(page_title="Smart Task Planner", page_icon="🤖", layout="wide")

# Configure the Google Generative AI model
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    MODEL = genai.GenerativeModel('gemini-pro')
except (AttributeError, KeyError):
    st.error("🚨 Google API Key not found. Please create a `.env` file with `GOOGLE_API_KEY='your_key'`.")
    st.stop()


# --- Core Logic ---

def generate_plan(goal):
    """
    Uses the LLM to generate a task plan based on the user's goal.

    Args:
        goal (str): The user-defined goal.

    Returns:
        dict: A dictionary containing the plan or an error message.
    """
    if not goal:
        return {"error": "Goal cannot be empty."}

    # This is the core prompt that instructs the LLM.
    # It requests a specific JSON structure for easy parsing.
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
        response = MODEL.generate_content(prompt)
        # Clean up the response to ensure it's a valid JSON string
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        plan = json.loads(cleaned_response)
        return plan
    except json.JSONDecodeError:
        return {"error": "AI returned an invalid format. Please try rephrasing your goal."}
    except Exception as e:
        # A catch-all for other potential API or generation errors
        return {"error": f"An unexpected error occurred: {e}"}

# --- Streamlit Frontend ---

st.title("🎯 Smart Task Planner")
st.write("Describe your goal, and let AI break it down into a manageable project plan.")

# User input
goal_input = st.text_input(
    "Enter your goal:",
    placeholder="e.g., Launch a new e-commerce mobile app in 3 months",
    key="goal_input"
)

# Generate Plan button
if st.button("Generate Plan", type="primary"):
    if goal_input:
        with st.spinner("🧠 AI is crafting your plan... This may take a moment."):
            generated_plan = generate_plan(goal_input)

        if "error" in generated_plan:
            st.error(generated_plan["error"])
        elif "plan" in generated_plan and generated_plan["plan"]:
            st.success("✅ Here's your action plan!")

            # Display tasks in a more readable and organized format
            tasks = generated_plan["plan"]

            # Sort tasks by ID for a logical flow
            sorted_tasks = sorted(tasks, key=lambda x: x['task_id'])

            for task in sorted_tasks:
                with st.expander(f"**Task {task['task_id']}: {task['task_name']}** ({task['duration_days']} days)"):
                    st.markdown(f"**Description:** {task['description']}")
                    dependencies = ", ".join(map(str, task['dependencies'])) if task['dependencies'] else "None"
                    st.markdown(f"**Dependencies:** This task depends on completing Task(s) **{dependencies}**.")

        else:
            st.warning("The AI couldn't generate a plan. Please try rephrasing your goal for better results.")
    else:
        st.warning("Please enter a goal to get started.")
