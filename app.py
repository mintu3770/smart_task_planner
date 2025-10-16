# app.py
import streamlit as st
import os
import json
from dotenv import load_dotenv

import google.generativeai as genai

# -------------------------
# Configuration and Setup
# -------------------------
load_dotenv()
st.set_page_config(page_title="Smart Task Planner", page_icon="🎯", layout="wide")

# --- API Key Configuration ---
try:
    API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.error("🚨 Missing Google API key. Please add it to your Streamlit Secrets.")
    st.stop()
except Exception as e:
    st.error(f"🚨 An error occurred during API configuration: {e}")
    st.stop()


# -------------------------
# Available Models
# -------------------------
AVAILABLE_MODELS = {
    "Gemini 2.0 Flash (Experimental) - Fastest": "models/gemini-2.0-flash-exp",
    "Gemini 2.5 Flash - Recommended": "models/gemini-2.5-flash",
    "Gemini 2.5 Pro - Most Capable": "models/gemini-2.5-pro",
    "Gemini 2.0 Flash - Stable": "models/gemini-2.0-flash",
}

# -------------------------
# Core Function
# -------------------------
def generate_plan(goal: str, model_name: str):
    """Generates a structured project plan from a user's goal using the Gemini API."""
    if not goal:
        return {"error": "Goal cannot be empty."}

    prompt = f"""
You are an expert project manager AI. Your task is to break down the user's goal into a structured action plan.
Goal: "{goal}"

Return ONLY a valid JSON object with this exact structure:
{{
  "plan": [
    {{
      "task_id": 1,
      "task_name": "Task name here",
      "description": "Detailed description here",
      "dependencies": [],
      "duration_days": 5
    }}
  ]
}}

Rules:
- task_id: integer starting from 1
- task_name: concise string
- description: detailed string
- dependencies: array of task_id integers (empty array if none)
- duration_days: integer

Provide a complete, logical breakdown of the goal into sequential tasks.
Return ONLY the JSON, no other text or markdown formatting.
"""
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # Generate content
        response = model.generate_content(
            contents=prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
        )

        # Parse the response
        response_text = response.text.strip()
        
        # Try to extract JSON if it's wrapped in markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif response_text.startswith("```"):
            lines = response_text.split("\n")
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    json_lines.append(line)
            response_text = "\n".join(json_lines).strip()
        
        try:
            plan_json = json.loads(response_text)
            # Basic validation to ensure the structure is correct
            if "plan" in plan_json and isinstance(plan_json["plan"], list):
                return plan_json
            else:
                 return {"error": "AI returned JSON in an unexpected format.", "raw": response_text}
        except json.JSONDecodeError as je:
            return {"error": f"AI failed to return valid JSON: {je}", "raw": response_text}

    except Exception as e:
        # Catch potential API errors
        return {"error": f"An error occurred while calling the AI model: {e}"}

# -------------------------
# Streamlit UI
# -------------------------
st.title("🎯 Smart Task Planner")
st.write(
    "Describe your high-level goal, and the AI will break it down into a "
    "detailed, structured action plan for you."
)

# Model selection
col1, col2 = st.columns([3, 1])

with col1:
    # Initialize session state for the input field
    if "goal_input" not in st.session_state:
        st.session_state.goal_input = "Launch a minimal e-commerce web app in 4 weeks."

    goal_input = st.text_input(
        "Enter your goal:",
        key="goal_input"
    )

with col2:
    selected_model_display = st.selectbox(
        "Select Model:",
        options=list(AVAILABLE_MODELS.keys()),
        index=0  # Default to Gemini 2.0 Flash Experimental
    )
    selected_model = AVAILABLE_MODELS[selected_model_display]

if st.button("Generate Plan", type="primary", use_container_width=True):
    if goal_input:
        with st.spinner("🧠 AI is thinking... Please wait."):
            result = generate_plan(goal_input, selected_model)

        if "error" in result:
            st.error(f'**Error:** {result["error"]}')
            if "raw" in result and result["raw"]:
                with st.expander("📟 View Raw AI Output"):
                    st.code(result["raw"], language="text")
        elif "plan" in result:
            tasks = result.get("plan", [])
            
            if not tasks:
                 st.warning("The AI generated an empty plan. Try a more specific goal.")
            else:
                st.success("✅ Here is your AI-generated action plan:")
                # Sort tasks by ID for a logical display order
                sorted_tasks = sorted(tasks, key=lambda x: x.get("task_id", 0))
                
                for task in sorted_tasks:
                    task_id = task.get('task_id', '?')
                    task_name = task.get('task_name', 'Unnamed Task')
                    duration = task.get('duration_days', '?')
                    dependencies = task.get("dependencies", [])
                    deps_str = ", ".join(map(str, dependencies)) if dependencies else "None"

                    with st.expander(f"**Task {task_id}: {task_name}** ({duration} days)"):
                        st.markdown(f"**Description:** {task.get('description', 'No description provided.')}")
                        st.markdown(f"**Dependencies:** Task(s) {deps_str}")
        else:
            st.warning("The AI did not return a valid plan. Please try rephrasing your goal.")
    else:
        st.warning("Please enter a goal first.")

# Footer
st.markdown("---")
st.caption(f"Using model: `{selected_model}`")
