# NextAI v2 — Text-to-SQL Chatbot & Event Analysis

Streamlit + Gemini + Supabase  
Next Capital · POC

## Features
1. **Text-to-SQL Chatbot**: แปลงคำถามภาษาธรรมชาติเป็น SQL query เพื่อดึงข้อมูลจาก Database อัตโนมัติ
2. **Event Extraction & Clustering**: สกัด "เหตุการณ์" (Agent, Predicate, Theme) จากข้อความอิสระ จัดกลุ่มด้วย Text Embeddings + KMeans และหาความผิดปกติ (Anomaly Detection)

## Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini (Flash / Pro)
- **Embeddings**: Gemini Text Embedding (`models/text-embedding-004`)
- **Machine Learning**: `scikit-learn` (สำหรับ KMeans Clustering)
- **Database**: Supabase Postgres (project `lmihffkslcdpgmehdqxe`)
- **Hosting**: Streamlit Community Cloud

## Setup (เรียงตามลำดับ)

### 1. รัน SQL setup ใน Supabase ครั้งเดียว
- เปิด Supabase Dashboard → SQL Editor → New query
- เปิดไฟล์ `supabase_setup.sql` → copy ทั้งหมด → paste → กด **Run**
- ทดสอบ: `SELECT execute_readonly_sql('SELECT COUNT(*) FROM contracts');` ต้องคืน `[{"count": 50}]`

### 2. Push code ขึ้น GitHub
```bash
git init
git add .
git commit -m "init NextAI v2"
git branch -M main
git remote add origin https://github.com/<USER>/<REPO>.git
git push -u origin main
```

(หรือใช้ GitHub web: New repo → Upload files → drag drop ทุกไฟล์)

### 3. Deploy บน Streamlit Cloud
1. ไปที่ https://share.streamlit.io → Login ด้วย GitHub
2. คลิก **New app** → เลือก repo → branch `main` → file `app.py`
3. คลิก **Advanced settings** → **Secrets** → paste:

```toml
GEMINI_API_KEY = "AIzaSy..."
SUPABASE_URL = "https://lmihffkslcdpgmehdqxe.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGc..."
```

4. คลิก **Deploy** → รอ 1-2 นาที → ได้ URL `https://<your-app>.streamlit.app`

### 4. Login
- Username: `CSTeam`
- Password: `12345678`

## Local development

```bash
# ติดตั้ง dependencies
pip install -r requirements.txt

# สร้าง secrets local
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# แก้ค่าใน secrets.toml

# รัน
streamlit run app.py
```

จะเปิด browser ที่ http://localhost:8501
หากต้องการใช้งานฟีเจอร์ Event Analysis ให้กดเลือกเมนู `event_analysis` ที่ Sidebar

## ปรับแต่ง

ทุก config อยู่ใน **`config.py`** — แก้แล้ว push GitHub → Streamlit จะ auto-redeploy

| ตัวแปร | ค่าที่ใช้ได้ |
|---|---|
| `OUTPUT_FORMAT['language']` | `thai` / `english` / `auto` |
| `OUTPUT_FORMAT['table_style']` | `dataframe` / `markdown` / `json` |
| `OUTPUT_FORMAT['summary']` | `none` / `bullet` / `paragraph` |
| `OUTPUT_FORMAT['row_limit']` | int (default 100) |
| `OUTPUT_FORMAT['show_sql']` | `True` / `False` |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` / `gemini-1.5-pro` |
| `APP_USER` / `APP_PASSWORD` | string |

System prompt + few-shot examples แก้ในไฟล์เดียวกัน

## โครงสร้างไฟล์

```
nextai-v2/
├── app.py                  # Streamlit main + chat UI + password gate
├── config.py               # ⭐ system prompt + output format
├── events.py               # Core logic สำหรับ Event Extraction & Clustering
├── llm.py                  # Gemini wrapper สำหรับ Text-to-SQL
├── db.py                   # Supabase client + SQL guardrails
├── requirements.txt
├── supabase_setup.sql      # รันครั้งเดียวก่อนใช้
├── .gitignore
├── pages/
│   └── event_analysis.py   # UI สำหรับหน้า Event Analysis
└── README.md
```

## Security notes

- SQL guardrail 2 ชั้น: Python regex + Postgres RPC function (block non-SELECT)
- Password เก็บใน `config.py` (plain text — เหมาะกับ POC เท่านั้น)
- RLS ของ Supabase ยังปิดอยู่ — สำหรับ production ควรเปิด + เขียน policy
- Anon key เป็น public โดย design — ปลอดภัยที่จะใส่ใน frontend ถ้ามี RLS

## Troubleshooting

**"function execute_readonly_sql does not exist"**  
→ ยังไม่ได้รัน `supabase_setup.sql` ใน Supabase

**"Permission denied for table contracts"**  
→ ลืม `GRANT SELECT` ใน setup script — รันใหม่

**Streamlit redeploy ไม่ทำงาน**  
→ ใน Streamlit Cloud → app menu → Reboot
