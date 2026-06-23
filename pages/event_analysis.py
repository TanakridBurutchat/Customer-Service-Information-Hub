import streamlit as st
import pandas as pd
import sys
import os

# Ensure parent directory is in path so we can import config & events
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import APP_USER, APP_PASSWORD
from events import process_events

st.set_page_config(
    page_title="Event Analysis",
    page_icon="🔎",
    layout="wide",
)

def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.title("🔒 NextAI v2 — Login")
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

st.title("🔎 Event Extraction & Analysis")
st.markdown("วิเคราะห์เหตุการณ์จากข้อความ (Event Extraction) และจัดกลุ่มเพื่อหาความผิดปกติ (Anomaly Detection)")

st.sidebar.markdown("### วิธีการทำงาน")
st.sidebar.markdown("1. รับข้อความ (ไทย/อังกฤษ)")
st.sidebar.markdown("2. ใช้ Gemini สกัด Agent, Predicate, Theme")
st.sidebar.markdown("3. ทำ Text Embedding ด้วย Gemini")
st.sidebar.markdown("4. จัดกลุ่มด้วย KMeans")
st.sidebar.markdown("5. คำนวณความน่าจะเป็น (Probability) เพื่อหาสิ่งผิดปกติ")

input_text = st.text_area(
    "📝 วางข้อความที่ต้องการวิเคราะห์ที่นี่ (ตัวอย่าง: ลูกค้า ก. โทรมาโวยวายพนักงาน คอลเซ็นเตอร์ และขอยกเลิกสัญญาทันที ส่วนลูกค้า ข. โทรมาสอบถามยอดค้างชำระปกติ ลูกค้า ค. โทรมาถามยอดค้างเช่นกัน)",
    height=200
)

col1, col2 = st.columns(2)
with col1:
    max_clusters = st.number_input("จำนวนกลุ่มสูงสุด (Max Clusters)", min_value=2, max_value=10, value=3)
with col2:
    st.write("") # padding
    st.write("")
    analyze_btn = st.button("🚀 วิเคราะห์เหตุการณ์", use_container_width=True)

if analyze_btn and input_text:
    with st.spinner("กำลังวิเคราะห์และจัดกลุ่ม..."):
        df = process_events(input_text, max_clusters=max_clusters)
        
        if df is not None and not df.empty:
            st.success(f"สกัดได้ {len(df)} เหตุการณ์")
            
            st.markdown("### 📊 ผลลัพธ์การวิเคราะห์")
            
            # Format display
            display_df = df.copy()
            if 'Probability' in display_df.columns:
                display_df['Probability'] = display_df['Probability'].apply(lambda x: f"{x:.2%}")
                
            st.dataframe(display_df, use_container_width=True)
            
            st.markdown("### 💡 การตีความ")
            st.info("- **Cluster**: เหตุการณ์ที่อยู่ในกลุ่มเดียวกัน จะมีความหมายคล้ายกัน\n- **Probability**: ยิ่งค่าน้อย แปลว่าเหตุการณ์นั้นเกิดได้ยาก หรือมีความ 'ผิดปกติ' (Anomaly) เมื่อเทียบกับเหตุการณ์อื่นๆ ในบริบทนี้")
        else:
            st.warning("ไม่สามารถสกัดเหตุการณ์ได้ ลองปรับข้อความให้ชัดเจนขึ้นครับ")
