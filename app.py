import streamlit as st
import os
import json
from dotenv import load_dotenv
import openai

# --- Configuration and Setup ---

# Load environment variables from .env file
load_dotenv()

# Set up page configuration for a better layout
st.set_page_config(page_title="Smart Task Planner", page_icon="🤖", layout="wide")

# --- CHANGE 1: Configure the client to use DeepSeek's API ---
try:
    client = openai.OpenAI(
        # The key name is now DEEPSEEK_API_KEY
        api_key=os.environ["DEEPSEEK_API_KEY"],
        # We point the client to DeepSeek's endpoint
        base_url="https://api.deepseek.com/v1"
    )
except (KeyError):
    # Update the error message to ask for the correct key
    st.error("🚨 DeepSeek API Key not found. Please add it to your Streamlit Secrets.")
    st.stop()


# --- Core Logic ---

def generate_plan(goal):
    """
    Uses the DeepSeek LLM to generate a task plan based on the user's goal.
    """
    if not goal:
        return {"error": "Goal cannot be empty."}

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
        # --- CHANGE 2: The API call now uses a DeepSeek model ---
        response = client.chat.completions.create(
            model="deepseek-chat",  # Use a powerful DeepSeek model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # Note: Not all models support JSON mode. If this fails, we may need to parse manually.
            # DeepSeek is generally good at following JSON instructions in the prompt.
            # response_format={"type": "json_object"} # Commenting out for broader compatibility
        )
        
        plan_json_string = response.choices[0].message.content
        # Clean up the response to ensure it's a valid JSON string
        cleaned_response = plan_json_string.strip().replace("```json", "").replace("```", "")
        plan = json.loads(cleaned_response)
        return plan

    except json.JSONDecodeError:
        return {"error": "AI returned an invalid format. Please try rephrasing your goal."}
    except Exception as e:
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

