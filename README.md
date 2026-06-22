# NextAI v2 — Text-to-SQL Chatbot

Streamlit + Gemini + Supabase  
Next Capital · POC

## Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini 2.0 Flash
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

## ปรับแต่ง

ทุก config อยู่ใน **`config.py`** — แก้แล้ว push GitHub → Streamlit จะ auto-redeploy

| ตัวแปร | ค่าที่ใช้ได้ |
|---|---|
| `OUTPUT_FORMAT['language']` | `thai` / `english` / `auto` |
| `OUTPUT_FORMAT['table_style']` | `dataframe` / `markdown` / `json` |
| `OUTPUT_FORMAT['summary']` | `none` / `bullet` / `paragraph` |
| `OUTPUT_FORMAT['row_limit']` | int (default 100) |
| `OUTPUT_FORMAT['show_sql']` | `True` / `False` |
| `GEMINI_MODEL` | `gemini-2.0-flash-exp` / `gemini-1.5-pro` |
| `APP_USER` / `APP_PASSWORD` | string |

System prompt + few-shot examples แก้ในไฟล์เดียวกัน ส่วน `build_system_prompt()`

## โครงสร้างไฟล์

```
nextai-v2/
├── app.py                  # Streamlit main + chat UI + password gate
├── config.py               # ⭐ system prompt + output format
├── llm.py                  # Gemini wrapper
├── db.py                   # Supabase client + SQL guardrails
├── requirements.txt
├── supabase_setup.sql      # รันครั้งเดียวก่อนใช้
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
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
