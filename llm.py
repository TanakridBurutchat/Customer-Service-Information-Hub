"""
Gemini LLM wrapper — text-to-SQL pipeline (2-pass)
Pass 1: user question -> SQL
Pass 2: SQL result -> natural language answer
"""
import re
import streamlit as st
import pandas as pd
import google.generativeai as genai
from config import GEMINI_MODEL, GEMINI_TEMPERATURE, build_system_prompt, build_answer_prompt


def _init_gemini():
    """Configure Gemini client once per session."""
    if "gemini_configured" not in st.session_state:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        st.session_state.gemini_configured = True


def get_model() -> genai.GenerativeModel:
    """Return cached GenerativeModel instance for SQL generation (pass 1)."""
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


def get_answer_model() -> genai.GenerativeModel:
    """Return cached GenerativeModel instance for natural-language answers (pass 2)."""
    _init_gemini()
    if "gemini_answer_model" not in st.session_state:
        st.session_state.gemini_answer_model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": 0.4,  # นิดหน่อยให้ดูเป็นธรรมชาติ ไม่แข็งทื่อ
                "max_output_tokens": 512,
            },
        )
    return st.session_state.gemini_answer_model


def generate_answer(user_question: str, history: list[dict] = None):
    """
    Pass 1: Stream Gemini response (SQL + brief explanation). Yields text chunks.
    """
    model = get_model()
    try:
        if history:
            chat = model.start_chat(history=history)
            stream = chat.send_message(user_question, stream=True)
        else:
            stream = model.generate_content(user_question, stream=True)
            
        for chunk in stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"\n\n❌ Gemini error: {str(e)[:300]}"


def _df_to_summary_text(df: pd.DataFrame, max_rows: int = 15) -> str:
    """Convert a result dataframe into compact text for the LLM to read."""
    if df is None or df.empty:
        return "(ไม่มีข้อมูล — query คืนค่าว่าง)"

    n_rows = len(df)
    n_cols = len(df.columns)

    # Special case: single cell result (e.g. COUNT(*))
    if n_rows == 1 and n_cols == 1:
        col = df.columns[0]
        val = df.iloc[0, 0]
        return f"คอลัมน์ '{col}' มีค่า = {val}"

    # Otherwise: show row count + sample rows as text
    preview = df.head(max_rows).to_dict(orient="records")
    more_note = f"\n(...และอีก {n_rows - max_rows} แถว)" if n_rows > max_rows else ""
    return f"จำนวนแถวทั้งหมด: {n_rows}\nตัวอย่างข้อมูล:\n{preview}{more_note}"


def generate_natural_answer(user_question: str, sql: str, df: pd.DataFrame, history: list[dict] = None) -> str:
    """
    Pass 2: Summarize the actual query result into natural Thai language.
    """
    result_summary = _df_to_summary_text(df)
    prompt = build_answer_prompt(user_question, sql, result_summary)

    model = get_answer_model()
    try:
        if history:
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt)
        else:
            response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"(สรุปคำตอบไม่สำเร็จ: {str(e)[:200]})"


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
    sql_match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if not sql_match:
        return None, text.strip()

    sql = sql_match.group(1).strip()
    remainder = text[sql_match.end():].strip()
    remainder = re.sub(r"^---\s*", "", remainder, flags=re.MULTILINE).strip()

    return sql, remainder
