import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core.ast_engine import StaticASTEngine
from core.groq_engine import GroqReviewOrchestrator
from groq import Groq

load_dotenv()

app = FastAPI(
    title="AI Code Reviewer Engine API",
    description="REST backend service providing AST static parsing and Groq LLM semantic code review.",
    version="1.0.0"
)

# --- Pydantic Data Models ---
class CodeSubmission(BaseModel):
    code: str = Field(..., description="Source code text to analyze.")
    language: str = Field(..., description="Programming language: Python, C, C++, or Java.")

class ReviewResponse(BaseModel):
    valid_syntax: bool
    health_score: int
    complexity_val: Any
    complexity_label: str
    time_complexity_before: str
    time_complexity_after: str
    static_issues: List[str]
    syntax_and_logic_bugs: List[str]
    code_smells_and_style: List[str]
    dsa_optimizations: List[str]
    optimized_code: str
    educational_breakdown: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatQuery(BaseModel):
    code_context: str
    language: str
    conversation: List[ChatMessage]

# --- Helper Function ---
def get_complexity_label(val: Any) -> str:
    if isinstance(val, (int, float)):
        if val <= 3:
            return f"Simple ({val} path{'s' if val > 1 else ''})"
        elif val <= 7:
            return f"Moderate ({val} paths)"
        else:
            return f"Complex ({val} paths)"
    return "N/A"

# --- API Endpoints ---
@app.get("/")
def home():
    return {"status": "online", "message": "API is running"}

@app.get("/health")
def health_check():
    return {"status": "online", "service": "code-review-fastapi"}

@app.post("/api/review", response_model=ReviewResponse)
def analyze_code_endpoint(payload: CodeSubmission):
    code = payload.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="Source code cannot be empty.")

    try:
        # 1. Deterministic local static AST check
        ast_report = StaticASTEngine.run_analysis(code, payload.language)

        # 2. Semantic & optimization review via Groq
        orchestrator = GroqReviewOrchestrator()
        ai_review = orchestrator.review(code, payload.language, ast_report)

        # 3. Calculate health metrics
        raw_cc = ast_report.get("metrics", {}).get("cyclomatic_complexity", 1)
        health_score = StaticASTEngine.calculate_health_score(
            len(ast_report["issues"]),
            len(ai_review.syntax_and_logic_bugs),
            raw_cc
        )

        return ReviewResponse(
            valid_syntax=ast_report["valid_syntax"],
            health_score=health_score,
            complexity_val=raw_cc,
            complexity_label=get_complexity_label(raw_cc),
            time_complexity_before=ai_review.time_complexity_before,
            time_complexity_after=ai_review.time_complexity_after,
            static_issues=ast_report["issues"],
            syntax_and_logic_bugs=ai_review.syntax_and_logic_bugs,
            code_smells_and_style=ai_review.code_smells_and_style,
            dsa_optimizations=ai_review.dsa_optimizations,
            optimized_code=ai_review.optimized_code,
            educational_breakdown=ai_review.educational_breakdown
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_doubt_endpoint(payload: ChatQuery):
    """Context-aware chatbot to explain code and answer doubts."""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set.")
            
        groq_client = Groq(api_key=api_key)

        system_instruction = f"""
You are an expert Computer Science tutor and code mentor.
The student has submitted this {payload.language} code for review:
{payload.code_context}
Answer the student's doubts directly, clearly, and concisely. 
Explain time/space complexity, data structure choices, or specific lines when asked. Keep answers beginner-friendly.
"""
        messages = [{"role": "system", "content": system_instruction}]
        for msg in payload.conversation:
            messages.append({"role": msg.role, "content": msg.content})

        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.3
        )
        return {"reply": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)