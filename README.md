# AI Code Reviewer

An AI-assisted code review tool that combines static analysis with LLM-generated suggestions to help developers understand potential issues and improve code quality.

**Live Demo:** [Open the deployed app](https://ai-codereviewer-app.streamlit.app/)  
**Source Code:** [GitHub Repository](https://github.com/bmanasareddy05/ai_code_reviewer)

## Features

- Review pasted or uploaded code in Python, C, C++, and Java.
- Run Python AST-based checks and heuristic checks for other supported languages.
- Request AI-generated explanations, code improvement suggestions, and complexity estimates.
- View diagnostics and code differences.
- Ask follow-up questions in the AI tutor chat and export a Markdown report.

## Tech Stack

Python · Streamlit · FastAPI · Groq API · Pydantic · Python AST

## Run Locally

1. Clone the repository and install dependencies:

   ```bash
   git clone https://github.com/bmanasareddy05/ai_code_reviewer.git
   cd ai_code_reviewer
   pip install -r requirements.txt
   ```

2. Create a `.env` file and add your Groq API key:

   ```env
   GROQ_API_KEY=your_groq_api_key
   BACKEND_API_URL=http://127.0.0.1:8000
   ```

3. Start the API in one terminal:

   ```bash
   uvicorn api:app --reload
   ```

4. Start the Streamlit app in another terminal:

   ```bash
   streamlit run app.py
   ```

## Important Notes

- Keep API keys in environment variables or your hosting provider's secrets settings. Never commit them to GitHub.
- Static checks for C, C++, and Java are heuristic, not full compiler analysis.
- AI-generated reviews and complexity estimates can be incorrect; review suggestions before using them.
- Submitted code is analyzed, not executed by the app.
