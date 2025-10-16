🎯 Smart Task Planner
A Python-based application that uses Large Language Models (LLMs) to break down high-level user goals into actionable, dependent tasks with estimated timelines. The frontend is built with Streamlit, and all generated plans are stored in a Supabase database for easy retrieval and management.
✨ Features

AI-Powered Reasoning: Leverages Google's Gemini models (including Gemini 2.5 Flash and Pro) to understand goals and generate logical task breakdowns.
Multiple Model Options: Choose from four different Gemini models based on your needs (speed vs capability).
Task Dependencies: Automatically identifies which tasks must be completed before others can begin.
Timeline Estimation: Provides an estimated duration in days for each task.
Database Integration: All generated plans are automatically saved to Supabase for future reference.
Plan History: Browse, search, and manage your previously generated plans.
Search Functionality: Quickly find past plans by searching goal keywords.
Interactive Frontend: A clean and intuitive user interface built with Streamlit to input goals and view generated plans.
Structured Output: The LLM is prompted to return clean JSON objects, ensuring reliable parsing and display.

🛠️ Tech Stack

Backend Logic: Python
AI Models: Google Gemini (2.0 Flash, 2.5 Flash, 2.5 Pro)
Frontend: Streamlit
Database: Supabase (PostgreSQL)
API Interaction: google-generativeai library
Database Client: supabase-py
Environment Management: python-dotenv

🚀 Getting Started
Follow these instructions to get a copy of the project up and running on your local machine.
Prerequisites

Python 3.8+
A Google API Key from Google AI Studio
A Supabase account and project (free tier available at supabase.com)

Installation & Setup

Clone the repository:

bash   git clone https://github.com/your-username/smart-task-planner.git
   cd smart-task-planner

Create a virtual environment:

bash   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

Install the required libraries:

bash   pip install -r requirements.txt

Set up Supabase:

Create a new project at supabase.com
Go to the SQL Editor and run the following SQL to create the required table:



sql     CREATE TABLE task_plans (
         id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
         goal TEXT NOT NULL,
         model_used TEXT NOT NULL,
         plan_json JSONB NOT NULL,
         created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
     );

     CREATE INDEX idx_task_plans_created_at ON task_plans(created_at DESC);

Get your Project URL and anon/public key from Project Settings → API


Set up your environment variables:

Create a new file named .env in the root of the project directory
Add your API keys and Supabase credentials:



env     GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
     SUPABASE_URL="https://your-project.supabase.co"
     SUPABASE_KEY="your_anon_public_key_here"

Run the application:

bash   streamlit run app.py

Open your browser:

Navigate to http://localhost:8501 (or the URL shown in your terminal)



📖 Usage
Generating a Plan

Navigate to the "Generate Plan" tab
Enter your high-level goal in the text input field
(Optional) Select a different AI model from the dropdown
Click "Generate Plan"
View your structured task breakdown with dependencies and timelines
The plan is automatically saved to your database

Viewing History

Navigate to the "Plan History" tab
Browse your 20 most recent plans
Use the search bar to find specific plans by goal keywords
Click on any plan to expand and view full details
Delete unwanted plans using the delete button

📦 Project Structure
smart-task-planner/
│
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not tracked in git)
├── .gitignore            # Git ignore file
└── README.md             # Project documentation
🔒 Security Notes

Never commit your .env file to version control
Keep your API keys and Supabase credentials secure
The Supabase anon key is safe for client-side use with Row Level Security (RLS) enabled
For production use, consider implementing user authentication and RLS policies

🚢 Deployment
Deploying to Streamlit Cloud

Push your code to GitHub (excluding .env)
Go to share.streamlit.io
Connect your GitHub repository
Add your secrets in the Streamlit Cloud dashboard:

toml   GOOGLE_API_KEY = "your_google_api_key_here"
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your_anon_public_key_here"

Deploy!

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the project
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.
🙏 Acknowledgments

Google Gemini for providing powerful AI models
Streamlit for the amazing web framework
Supabase for the open-source database solution

📧 Contact
Your Name - @your_twitter - your.email@example.com
Project Link: https://github.com/your-username/smart-task-planner
