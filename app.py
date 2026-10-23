import difflib
import requests
import streamlit as st
import os

st.set_page_config(
    page_title="CodeReview AI | Automated Code Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dynamically pick up the deployed backend URL or default to localhost
BACKEND_BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000").rstrip("/")
FASTAPI_URL = f"{BACKEND_BASE_URL}/api/review"
FASTAPI_CHAT_URL = f"{BACKEND_BASE_URL}/api/chat"
# Dark theme styling
st.markdown("""
<style>
    /* Adaptive Metric Cards (works in both Light & Dark themes) */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        padding: 12px 14px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricLabel"] {
        white-space: normal !important;
        overflow: visible !important;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: var(--text-color) !important;
        opacity: 0.75;
        margin-bottom: 2px;
        white-space: normal !important;
    }
    div[data-testid="stMetricValue"] {
        white-space: normal !important;
        overflow: visible !important;
    }
    div[data-testid="stMetricValue"] div {
        font-size: 19px !important;
        font-weight: 700 !important;
        color: var(--text-color) !important;
        white-space: normal !important;
        text-overflow: clip !important;
        overflow: visible !important;
    }

    /* Subheadings: automatically adapts to light or dark background */
    .section-title {
        font-size: 16px;
        font-weight: 700;
        color: var(--text-color) !important;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    /* Diagnostic boxes with readable text in both themes */
    .diagnostic-box {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-size: 14px;
        line-height: 1.5;
        border-left: 4px solid;
    }
    .box-danger {
        background-color: rgba(239, 68, 68, 0.1);
        border-left-color: #ef4444;
        color: #b91c1c;
    }
    .box-warning {
        background-color: rgba(245, 158, 11, 0.1);
        border-left-color: #f59e0b;
        color: #b45309;
    }
    .box-info {
        background-color: rgba(59, 130, 246, 0.1);
        border-left-color: #3b82f6;
        color: #1d4ed8;
    }
    .box-success {
        background-color: rgba(34, 197, 94, 0.1);
        border-left-color: #22c55e;
        color: #15803d;
    }

    /* Keep high-contrast text if user explicitly switches to dark mode */
    @media (prefers-color-scheme: dark) {
        .box-danger { color: #fca5a5; }
        .box-warning { color: #fcd34d; }
        .box-info { color: #93c5fd; }
        .box-success { color: #86efac; }
    }
</style>
""", unsafe_allow_html=True)

st.title("CodeReview AI")
st.caption("Microservice Architecture: FastAPI Backend + Streamlit UI + Interactive Tutor")

# Maintain session state
if "review_data" not in st.session_state:
    st.session_state.review_data = None
if "current_code" not in st.session_state:
    st.session_state.current_code = ""
if "current_lang" not in st.session_state:
    st.session_state.current_lang = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

def reset_review_state():
    st.session_state.review_data = None
    st.session_state.messages = []

st.sidebar.markdown("### Settings")
language = st.sidebar.selectbox(
    "Programming Language",
    ["Python", "C", "C++", "Java"],
    key="selected_language",
    on_change=reset_review_state
)
input_mode = st.sidebar.radio("Input Mode", ["Paste Code", "Upload File"])

code_presets = {
    "Python": """import math

def calculate_factors(n):
    factors = []
    # Inefficient O(N) search with unneeded variables
    temp_counter = 0
    for i in range(1, n + 1):
        if n % i == 0:
            factors.append(i)
    return factors
""",
    "C": """#include <stdio.h>
#include <stdlib.h>

void process_data() {
    int *arr = (int*)malloc(100 * sizeof(int));
    // Memory leak: arr is never freed
    for (int i = 0; i < 100; i++) {
        arr[i] = i * 2;
    }
}

int main() {
    process_data();
    return 0;
}
""",
    "C++": """#include <iostream>
#include <vector>

void printDuplicates(const std::vector<int>& vec) {
    // Inefficient O(N^2) brute force
    for (size_t i = 0; i < vec.size(); i++) {
        for (size_t j = i + 1; j < vec.size(); j++) {
            if (vec[i] == vec[j]) {
                std::cout << vec[i] << " ";
            }
        }
    }
}
""",
    "Java": """public class StringConcatDemo {
    // Inefficient string concatenation inside loop
    public static String buildLog(int count) {
        String output = "";
        for (int i = 0; i < count; i++) {
            output += "entry_" + i + ";";
        }
        return output;
    }
}
"""
}

code_input = ""
if input_mode == "Paste Code":
    code_input = st.text_area(f"Source Code ({language})", value=code_presets[language], height=220)
else:
    file_extensions = {"Python": ["py"], "C": ["c", "h"], "C++": ["cpp", "hpp"], "Java": ["java"]}
    uploaded_file = st.file_uploader(f"Upload a {language} file", type=file_extensions.get(language, []))
    if uploaded_file is not None:
        code_input = uploaded_file.read().decode("utf-8")
        st.code(code_input, language=language.lower())
    else:
        st.info("Select a source file to analyze.")

if st.button("Run Code Review", type="primary", use_container_width=True):
    if not code_input.strip():
        st.error("Please enter code before running analysis.")
    else:
        with st.spinner("Connecting to FastAPI backend & analyzing..."):
            try:
                response = requests.post(
                    FASTAPI_URL,
                    json={"code": code_input, "language": language},
                    timeout=45
                )

                if response.status_code != 200:
                    st.error(f"Backend API Error: {response.json().get('detail', response.text)}")
                else:
                    st.session_state.review_data = response.json()
                    st.session_state.current_code = code_input
                    st.session_state.current_lang = language
                    st.session_state.messages = []
                    st.success("Review complete via FastAPI service.")

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to FastAPI server. Please run: python -m uvicorn api:app --reload --port 8000")
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")

# Render Results
if st.session_state.review_data:
    data = st.session_state.review_data
    t_before = data["time_complexity_before"].split()[0] if data["time_complexity_before"] else "N/A"
    t_after = data["time_complexity_after"].split()[0] if data["time_complexity_after"] else "N/A"
    cc_value = data.get("complexity_val", 1)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric(
            "Health Score",
            f"{data['health_score']}/100",
            help="Overall code quality calculated from static defects, style warnings, and cyclomatic complexity."
        )
    with m2:
        st.metric(
            "Syntax Status",
            "Passed" if data["valid_syntax"] else "Failed",
            help="AST validation confirming proper syntax grammar, tokens, and balanced enclosures."
        )
    with m3:
        st.metric(
            "Complexity",
            f"M = {cc_value}",
            help=f"Cyclomatic complexity ({data['complexity_label']}): counts linearly independent execution paths through source code. Lower is better."
        )
    with m4:
        st.metric(
            "Initial Time",
            t_before,
            help="Estimated asymptotic runtime complexity (Big-O) of the submitted code."
        )
    with m5:
        st.metric(
            "Optimized Time",
            t_after,
            help="Target asymptotic runtime complexity (Big-O) achieved in the refactored solution."
        )

    st.write("")

    tab_overview, tab_diff, tab_chat, tab_export = st.tabs([
        "Diagnostics & Fixes",
        "Code Comparison (Diff)",
        "💬 Ask Doubts (AI Tutor)",
        "Export Report"
    ])

    with tab_overview:
        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.markdown('<div class="section-title">Static & Logic Issues</div>', unsafe_allow_html=True)
            for issue in data["static_issues"]:
                st.markdown(f'<div class="diagnostic-box box-danger"><strong>Static AST:</strong> {issue}</div>', unsafe_allow_html=True)

            for bug in data["syntax_and_logic_bugs"]:
                st.markdown(f'<div class="diagnostic-box box-warning"><strong>Logic Issue:</strong> {bug}</div>', unsafe_allow_html=True)

            if not data["static_issues"] and not data["syntax_and_logic_bugs"]:
                st.markdown('<div class="diagnostic-box box-success">No critical syntax, memory leaks, or structural violations detected.</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-title">Coding Standards & Smells</div>', unsafe_allow_html=True)
            for style in data["code_smells_and_style"]:
                st.markdown(f'<div class="diagnostic-box box-info"><strong>Style Note:</strong> {style}</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-title">Algorithmic Recommendations</div>', unsafe_allow_html=True)
            for opt in data["dsa_optimizations"]:
                st.markdown(f"• {opt}")

        with col_right:
            st.markdown('<div class="section-title">Refactored Implementation</div>', unsafe_allow_html=True)
            st.code(data["optimized_code"], language=st.session_state.current_lang.lower())

            st.markdown('<div class="section-title">Explanation & Mentor Notes</div>', unsafe_allow_html=True)
            st.info(data["educational_breakdown"])

    with tab_diff:
        st.markdown("#### Line-by-Line Changes")
        diff = difflib.unified_diff(
            st.session_state.current_code.splitlines(keepends=True),
            data["optimized_code"].splitlines(keepends=True),
            fromfile="submitted_code",
            tofile="optimized_code"
        )
        diff_text = "".join(diff)
        if diff_text:
            st.code(diff_text, language="diff")
        else:
            st.info("No line modifications needed; code is already optimal.")

    with tab_chat:
        st.markdown("#### 💬 Ask Questions About Your Code")
        st.caption("Ask questions about optimizations, complexities, or specific lines.")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if user_prompt := st.chat_input("Ask a doubt (e.g., 'Why is my solution inefficient?'):"):
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        chat_res = requests.post(
                            FASTAPI_CHAT_URL,
                            json={
                                "code_context": f"ORIGINAL:\n{st.session_state.current_code}\n\nREFACTORED:\n{data['optimized_code']}",
                                "language": st.session_state.current_lang,
                                "conversation": st.session_state.messages
                            },
                            timeout=30
                        )
                        if chat_res.status_code == 200:
                            bot_reply = chat_res.json()["reply"]
                            st.markdown(bot_reply)
                            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                        else:
                            st.error("Error communicating with AI tutor.")
                    except Exception as err:
                        st.error(f"Chat error: {str(err)}")

    with tab_export:
        st.markdown("#### Download Summary")
        all_issues = data["static_issues"] + data["syntax_and_logic_bugs"]
        issues_md = "\n".join([f"- {issue}" for issue in all_issues]) if all_issues else "None detected"
        styles_md = "\n".join([f"- {s}" for s in data["code_smells_and_style"]]) if data["code_smells_and_style"] else "Compliant"
        opts_md = "\n".join([f"- {opt}" for opt in data["dsa_optimizations"]]) if data["dsa_optimizations"] else "Already optimal"

        report_md = f"""# Code Review Report
Language: {st.session_state.current_lang}
Health Score: {data['health_score']}/100
Complexity: {data['complexity_label']}
Time Complexity: {data['time_complexity_before']} -> {data['time_complexity_after']}

Issues Detected:
{issues_md}

Style & Conventions:
{styles_md}

Algorithmic Improvements:
{opts_md}

Refactored Code:
{data['optimized_code']}

Educational Explanation:
{data['educational_breakdown']}
"""
        st.download_button(
            label="Download Report (.md)",
            data=report_md,
            file_name=f"code_review_{st.session_state.current_lang.lower()}.md",
            mime="text/markdown",
            use_container_width=True
        )