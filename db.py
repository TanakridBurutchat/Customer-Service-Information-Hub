"""
Database layer — Supabase client + SQL safety guardrails
"""
import re
import streamlit as st
from supabase import create_client, Client
import pandas as pd


# Banned SQL keywords (case-insensitive, whole-word match)
FORBIDDEN_KEYWORDS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b",
    r"\bDROP\b", r"\bALTER\b", r"\bTRUNCATE\b",
    r"\bCREATE\b", r"\bGRANT\b", r"\bREVOKE\b",
    r"\bMERGE\b", r"\bCOPY\b", r"\bEXECUTE\b",
    r";\s*--",   # SQL comment injection
]


def get_supabase_client() -> Client:
    """Cached Supabase client. Reads creds from Streamlit secrets."""
    if "supabase_client" not in st.session_state:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Returns (is_safe, error_message).
    Block any non-SELECT statement & dangerous keywords.
    """
    cleaned = sql.strip().rstrip(";").strip()

    if not cleaned:
        return False, "SQL ว่างเปล่า"

    # Must start with SELECT or WITH (CTE)
    first_word = cleaned.split(None, 1)[0].upper()
    if first_word not in ("SELECT", "WITH"):
        return False, f"อนุญาตเฉพาะ SELECT/WITH เท่านั้น (พบ: {first_word})"

    # Check forbidden keywords
    for pattern in FORBIDDEN_KEYWORDS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            kw = pattern.replace(r"\b", "").replace(r"\s*--", "comment injection")
            return False, f"พบ keyword ที่ไม่อนุญาต: {kw}"

    return True, ""


def execute_sql(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """
    Run SQL via Supabase RPC. Returns (dataframe, error_message).
    Requires an RPC function `execute_readonly_sql` to be created in Supabase
    (see supabase_setup.sql).
    """
    is_safe, err = validate_sql(sql)
    if not is_safe:
        return None, f"❌ SQL ถูกบล็อก: {err}"

    # สำคัญ: ตัด ; ท้าย query ก่อนส่งไป Supabase
    # เพราะ RPC ห่อ query ด้วย subquery แบบ "SELECT json_agg(t) FROM (%s) t"
    # ถ้ามี ; หลุดเข้าไปข้างใน parentheses จะกลายเป็น syntax error
    cleaned_sql = sql.strip().rstrip(";").strip()

    client = get_supabase_client()

    try:
        result = client.rpc("execute_readonly_sql", {"query_text": cleaned_sql}).execute()
        data = result.data

        if data is None or (isinstance(data, list) and len(data) == 0):
            return pd.DataFrame(), None

        df = pd.DataFrame(data)
        return df, None

    except Exception as e:
        return None, f"❌ Database error: {str(e)[:300]}"
