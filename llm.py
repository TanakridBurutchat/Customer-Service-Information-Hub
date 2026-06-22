"""
Gemini LLM wrapper — text-to-SQL pipeline
"""
import re
import streamlit as st
import google.generativeai as genai
from config import GEMINI_MODEL, GEMINI_TEMPERATURE, build_system_prompt


def _init_gemini():
    """Configure Gemini client once per session."""
    if "gemini_configured" not in st.session_state:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        st.session_state.gemini_configured = True


def get_model() -> genai.GenerativeModel:
    """Return cached GenerativeModel instance."""
    _init_gemini()
    if "gemini_model" not in st.session_state:
        st.session_state.gemini_model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=build_system_prompt(),
            generation_config={
                "temperature": GEMINI_TEMPERATURE,
                "max_output_tokens": 2048,
            },
        )
    return st.session_state.gemini_model


def generate_answer(user_question: str):
    """
    Stream Gemini response. Yields text chunks.
    """
    model = get_model()
    try:
        stream = model.generate_content(user_question, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"\n\n❌ Gemini error: {str(e)[:300]}"


def parse_response(text: str) -> tuple[str | None, str]:
    """
    Split LLM output into (sql, explanation).
    Expected format:
        ```sql
        SELECT ...
        ```
        ---
        explanation text
    """
    # Try to extract SQL from code block
    sql_match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if not sql_match:
        # No SQL found — likely OUT_OF_SCOPE
        return None, text.strip()

    sql = sql_match.group(1).strip()

    # Get text after the SQL block (and after --- if present)
    remainder = text[sql_match.end():].strip()
    remainder = re.sub(r"^---\s*", "", remainder, flags=re.MULTILINE).strip()

    return sql, remainder
