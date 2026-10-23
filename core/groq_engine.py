import json
import os
from typing import List
from groq import Groq
from pydantic import BaseModel, Field, AliasChoices
from dotenv import load_dotenv

load_dotenv()


class ReviewResult(BaseModel):
    syntax_and_logic_bugs: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "syntax_and_logic_bugs", "syntax_logic_issues", "syntax_errors", "errors", "bugs"
        )
    )
    code_smells_and_style: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "code_smells_and_style", "style_issues", "code_smells", "style_guidelines", "style"
        )
    )
    dsa_optimizations: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "dsa_optimizations", "optimizations", "algorithmic_optimizations", "dsa_improvements"
        )
    )
    time_complexity_before: str = Field(
        default="N/A",
        validation_alias=AliasChoices("time_complexity_before", "complexity_before", "initial_complexity")
    )
    time_complexity_after: str = Field(
        default="N/A",
        validation_alias=AliasChoices("time_complexity_after", "complexity_after", "optimized_complexity")
    )
    optimized_code: str = Field(
        default="",
        validation_alias=AliasChoices("optimized_code", "improved_code", "refactored_code", "code")
    )
    educational_breakdown: str = Field(
        default="",
        validation_alias=AliasChoices("educational_breakdown", "explanation", "pedagogical_breakdown", "breakdown")
    )


class GroqReviewOrchestrator:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment or .env file.")
        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"

    def review(self, code: str, language: str, static_ast_report: dict) -> ReviewResult:
        prompt = f"""
You are an expert compiler engineer, systems architect, and senior academic evaluator.
Perform a strict code review on the following {language} code submission.

STATIC DIAGNOSTIC SIGNALS DETECTED BY LOCAL SCANNER:
- Detected Static Issues: {static_ast_report.get('issues', [])}
- Computed Metrics: {static_ast_report.get('metrics', {})}

TARGET CODE UNDER REVIEW:
```{language.lower()}
{code}
CRITICAL INSTRUCTION:
You must respond ONLY with a single JSON object. The JSON keys MUST strictly match the following schema:
{{
"syntax_and_logic_bugs": ["string"],
"code_smells_and_style": ["string"],
"dsa_optimizations": ["string"],
"time_complexity_before": "O(...)",
"time_complexity_after": "O(...)",
"optimized_code": "string with the complete refactored source code",
"educational_breakdown": "string with detailed explanation"
}}
"""

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a code review engine. You must output a JSON object adhering exactly to the requested key names."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        content = completion.choices[0].message.content.strip()
        
        # Clean any markdown fences if present
        if content.startswith("```"):
            content = content.strip("`").replace("json\n", "", 1).strip()

        return ReviewResult.model_validate_json(content)