import streamlit as st
import os
import json
from dotenv import load_dotenv

# --- CHANGE 1: Import the OpenAI library ---
import openai

# --- Configuration and Setup ---

# Load environment variables from .env file
load_dotenv()

# Set up page configuration for a better layout
st.set_page_config(page_title="Smart Task Planner", page_icon="🤖", layout="wide")

# --- CHANGE 2: Configure the OpenAI client ---
try:
    # It's best practice to use the OpenAI client
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
except (KeyError):
    st.error("🚨 OpenAI API Key not found. Please add it to your Streamlit Secrets.")
    st.stop()


# --- Core Logic ---

def generate_plan(goal):
    """
    Uses the OpenAI LLM to generate a task plan based on the user's goal.
    """
    if not goal:
        return {"error": "Goal cannot be empty."}

    # --- CHANGE 3: The prompt is now structured for OpenAI's Chat Completions API ---
    # We use a "system" message to set the AI's persona and a "user" message for the specific request.
    system_prompt = """
    You are an expert project manager AI. Your task is to break down a complex user goal into a detailed, actionable plan.
    Generate a plan as a structured JSON object. The JSON object must have a single key "plan" which is an array of task objects.
    Each task object must have the following keys:
    - "task_id": A unique integer identifier for the task, starting from 1.
    - "task_name": A concise, actionable name for the task.
    - "description": A brief explanation of what the task involves and why it's important.
    - "dependencies": An array of `task_id`s that this task depends on. An empty array [] means it has no dependencies.
    - "duration_days": An estimated integer for the number of days required to complete the task.
    Provide only the raw JSON output, without any introductory text, closing text, or markdown formatting like ```json.
    """
    
    user_prompt = f"The user's goal is: \"{goal}\""

    try:
        # --- CHANGE 4: The API call is now to OpenAI ---
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # A powerful and cost-effective model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"} # Use JSON mode for reliable output
        )
        
        # The response from OpenAI is in a different format
        plan_json_string = response.choices[0].message.content
        plan = json.loads(plan_json_string)
        return plan

    except json.JSONDecodeError:
        return {"error": "AI returned an invalid format. Please try rephrasing your goal."}
    except Exception as e:
        # A catch-all for other potential API or generation errors
        return {"error": f"An unexpected error occurred: {e}"}

# --- Streamlit Frontend (No changes needed below this line) ---

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
            tasks = generated_plan["plan"]
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
