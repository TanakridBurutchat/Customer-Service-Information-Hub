"""
NextAI v2 — Text-to-SQL Chatbot
Streamlit main app
"""
import json
import io
import streamlit as st
import pandas as pd

from config import APP_USER, APP_PASSWORD, OUTPUT_FORMAT
from llm import generate_answer, parse_response, generate_natural_answer
from db import execute_sql


st.set_page_config(
    page_title="NextAI v2",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ──────────────────────────────────────────────────────────────────────
# Password gate
# ──────────────────────────────────────────────────────────────────────
def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.title("🔒 NextAI v2 — Login")
    st.caption("Next Capital — Customer Service Team")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        if username == APP_USER and password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Username หรือ Password ไม่ถูกต้อง")
    return False


if not check_password():
    st.stop()


# ──────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────
col_a, col_b = st.columns([5, 1])
with col_a:
    st.title("💬 NextAI v2")
    st.caption("Text-to-SQL Chatbot · Gemini · Supabase")
with col_b:
    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ──────────────────────────────────────────────────────────────────────
# Sidebar: example questions
# ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("💡 ลองถามคำถามเหล่านี้")
    examples = [
        "มีสัญญาทั้งหมดกี่สัญญา",
        "ลูกค้าค้างชำระกี่คน",
        "สรุปสถานะสัญญาทั้งระบบ",
        "หาลูกค้าชื่อวิชา ผ่อนถึงงวดไหน",
        "ลูกค้าที่ประกัน PA หมดอายุภายใน 6 เดือนนี้",
        "งวดที่ค้างเกิน 60 วันมีกี่งวด",
        "สัญญาทั้งหมดที่ยังไม่ปิดบัญชี",
        "ลูกค้าที่ยังไม่ได้ซื้อ PA",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.pending_question = ex
            st.rerun()

    st.divider()
    st.caption("Output format (อ่านได้อย่างเดียว)")
    st.code(f"language: {OUTPUT_FORMAT['language']}\n"
            f"table:    {OUTPUT_FORMAT['table_style']}\n"
            f"summary:  {OUTPUT_FORMAT['summary']}", language="yaml")
            
    st.divider()
    if st.button("🧹 ล้างประวัติแชท (Clear Chat)", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ──────────────────────────────────────────────────────────────────────
# Chat history state
# ──────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []


def is_single_value_result(df: pd.DataFrame) -> bool:
    """True if result is just 1 row x 1 column (e.g. a COUNT(*))."""
    return df is not None and not df.empty and df.shape == (1, 1)


def render_table(df: pd.DataFrame):
    """Render result table according to OUTPUT_FORMAT['table_style'].
    Skips rendering entirely for single-value results — those are
    already spoken in the natural-language answer, a table would be
    redundant clutter."""
    if df is None or df.empty:
        return
    if is_single_value_result(df):
        return  # the number is already in the spoken answer

    style = OUTPUT_FORMAT["table_style"]
    if style == "dataframe":
        st.dataframe(df, use_container_width=True, hide_index=True)
    elif style == "markdown":
        st.markdown(df.to_markdown(index=False))
    elif style == "json":
        st.json(df.to_dict(orient="records"))
    else:
        st.dataframe(df, use_container_width=True)


def render_history_item(msg: dict):
    """Render a past chat message."""
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            if msg.get("error"):
                st.error(msg["error"])
            else:
                if msg.get("natural_answer"):
                    st.markdown(msg["natural_answer"])
                if msg.get("df_json") is not None:
                    df = pd.read_json(io.StringIO(msg["df_json"]), orient="split")
                    render_table(df)
            if msg.get("sql") and OUTPUT_FORMAT["show_sql"]:
                with st.expander("📜 SQL ที่ใช้", expanded=False):
                    st.code(msg["sql"], language="sql")


# ──────────────────────────────────────────────────────────────────────
# Render chat history
# ──────────────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    render_history_item(msg)


# ──────────────────────────────────────────────────────────────────────
# Input handling
# ──────────────────────────────────────────────────────────────────────
user_input = st.chat_input("พิมพ์คำถามของคุณ (ภาษาไทย/อังกฤษ)...")

# Pre-fill from sidebar example click
if not user_input and "pending_question" in st.session_state:
    user_input = st.session_state.pop("pending_question")


if user_input:
    # Build short-term memory (last 4 messages)
    gemini_history = []
    for m in st.session_state.messages[-4:]:
        role = "user" if m["role"] == "user" else "model"
        content = m["content"] if role == "user" else (m.get("natural_answer") or "...")
        gemini_history.append({"role": role, "parts": [content]})

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Stream assistant response
    with st.chat_message("assistant"):
        # ── Pass 1: generate SQL (streamed, shown inside a collapsing status) ──
        with st.status("🧠 กำลังคิด...", expanded=False) as status:
            placeholder = st.empty()
            full_text = ""
            for chunk in generate_answer(user_input, history=gemini_history):
                full_text += chunk
                placeholder.markdown(full_text + "▌")
            placeholder.markdown(full_text)
            status.update(label="✅ คิดเสร็จ", state="complete")

        sql, _raw_explanation = parse_response(full_text)

        msg_record = {
            "role": "assistant",
            "sql": sql,
            "natural_answer": None,
            "df_json": None,
            "error": None,
        }

        if sql is None:
            warning_text = _raw_explanation or "ขออภัยครับ ไม่สามารถตอบคำถามนี้ได้ในระบบนี้ครับ"
            st.warning(warning_text)
            msg_record["natural_answer"] = warning_text
            msg_record["error"] = "OUT_OF_SCOPE"
        else:
            with st.spinner("🔍 กำลังค้นข้อมูล..."):
                df, db_err = execute_sql(sql)

            if db_err:
                st.error(db_err)
                msg_record["error"] = db_err
            else:
                # ── Pass 2: turn the real result into a friendly Thai answer ──
                with st.spinner("✍️ กำลังสรุปคำตอบ..."):
                    natural_answer = generate_natural_answer(user_input, sql, df, history=gemini_history)

                st.markdown(natural_answer)
                render_table(df)

                msg_record["natural_answer"] = natural_answer
                msg_record["df_json"] = df.to_json(orient="split", force_ascii=False)

            if OUTPUT_FORMAT["show_sql"] and sql:
                with st.expander("📜 SQL ที่ใช้", expanded=False):
                    st.code(sql, language="sql")

        st.session_state.messages.append(msg_record)

        # ── Long-Term Memory: Save to Supabase ──
        try:
            from db import get_supabase_client
            client = get_supabase_client()
            client.table("chat_logs").insert({
                "username": APP_USER,
                "user_question": user_input,
                "generated_sql": msg_record.get("sql"),
                "natural_answer": msg_record.get("natural_answer"),
                "error_message": msg_record.get("error")
            }).execute()
        except Exception as e:
            st.toast(f"Warning: Failed to save log to Supabase: {e}")
