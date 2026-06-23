"""
NextAI v2 — Centralized Config

แก้ตัวแปรในไฟล์นี้แล้ว push GitHub → Streamlit จะ auto-redeploy
ไม่ต้องแก้ไฟล์อื่น
"""

# ──────────────────────────────────────────────────────────────────────
# OUTPUT FORMAT — แก้ตรงนี้เพื่อเปลี่ยนรูปแบบคำตอบ
# ──────────────────────────────────────────────────────────────────────
OUTPUT_FORMAT = {
    # ภาษาคำตอบ: "thai" / "english" / "auto" (auto = ตามภาษา input)
    "language": "thai",

    # รูปแบบตารางผลลัพธ์: "dataframe" / "markdown" / "json"
    #   dataframe = Streamlit interactive (เรียง / search ได้)
    #   markdown  = ตาราง markdown (อ่านง่าย copy ได้)
    #   json      = raw JSON (สำหรับ dev)
    "table_style": "dataframe",

    # รูปแบบสรุป: "none" / "bullet" / "paragraph"
    "summary": "bullet",

    # Row limit (ป้องกัน query ดึงข้อมูลเยอะเกิน)
    "row_limit": 100,

    # โชว์ SQL ที่ LLM gen ใน UI ไหม
    "show_sql": True,
}

# ──────────────────────────────────────────────────────────────────────
# GEMINI MODEL
# ──────────────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-3.1-flash-lite"   # เร็ว + ฟรี tier ใหญ่
# GEMINI_MODEL = "gemini-1.5-pro"       # ฉลาดกว่า แต่ช้ากว่า + จำกัด quota
GEMINI_TEMPERATURE = 0.1                 # ต่ำ = SQL คงเส้นคงวา ไม่มั่ว

# ──────────────────────────────────────────────────────────────────────
# AUTHENTICATION (Password Gate)
# ──────────────────────────────────────────────────────────────────────
APP_USER = "CSTeam"
APP_PASSWORD = "12345678"

# ──────────────────────────────────────────────────────────────────────
# DATABASE SCHEMA (สำหรับให้ LLM อ่าน)
# ──────────────────────────────────────────────────────────────────────
DB_SCHEMA = """
# Database: Next Capital (PostgreSQL on Supabase)

## Master table
- **contracts** (PK: contract_no) — สัญญาเช่าซื้อทั้งหมด ศูนย์กลางของระบบ
  - contract_no (TEXT, 12 หลัก) | customer_name | customer_idcard
  - product_type ('รถจักรยานยนต์' / 'รถยนต์' / 'รถยนต์มือสอง' / 'เครื่องใช้ไฟฟ้า')
  - contract_date (DATE) | principal_amount (NUMERIC) | hire_purchase_period (INT)
  - branch_no (TEXT, '400'–'440') | source

## Payment tables
- **installment_schedule** (FK: contract_no) — รายงวด
  - installment_no (INT) | due_date | installment_amount | paid_amount
  - paid_date | late_fee | status ('PAID' / 'PENDING' / 'OVERDUE' / 'WAIVED')
  - UNIQUE (contract_no, installment_no)

- **contract_payment_summary** (PK: contract_no, 1:1) — สรุปต่อสัญญา
  - total_installments | paid_installments | remaining_installments
  - total_amount | paid_amount | remaining_amount
  - next_due_date | next_due_amount | overdue_installments
  - contract_status ('NORMAL' / 'LATE' / 'DEFAULT' / 'CLOSED')
  - last_payment_date

## Insurance & documents
- **pa_insurance_policies** (FK: contractno — NO underscore!) — ประกัน PA/PLUS
  - refno_temporaryno (UNIQUE) | assured_firstname / lastname | assured_idcard
  - productcode ('PA 3 YEAR' / 'PA PLUS 3 YEAR')
  - effectivedate | expireddate | insured | totalpremium
  - card_expiry_date | delivery_date | + 30 more columns

- **closure_letters** (FK: contract_no) — จดหมายปิดบัญชี
  - letter_type ('Mail' / 'WO' / 'RL') | letter_date | tracking_no | sent_date

- **lockton_tax_plates** (FK: contract_no, UQ: policy_no) — ป้ายภาษีส่ง Lockton
  - vehicle_registration | purchase_date | sent_date | is_revised (BOOL)

- **mailing_documents** (FK: contract_no, UQ: document_no) — จัดส่งเอกสาร
  - product ('NewMC' / 'Next money') | branch | receive_date

- **branch_delivery** (FK: contract_no) — ส่งสาขา
- **guarantor_address** (FK: contract_no) — คนค้ำประกัน (1 สัญญามีได้หลายคน)
- **returned_documents** (FK: contract_no) — เอกสารตีกลับ
- **tracking_update_import** (FK: contract_no, UQ: request_id)

## ⭐ View หลัก: v_contract_360
LEFT JOIN ทุกตารางผ่าน contract_no — ใช้ตอบคำถามเกี่ยวกับลูกค้าเดี่ยวได้ทันที
Columns:
  contract_no, customer_name, customer_idcard, product_type, contract_date,
  principal_amount, hire_purchase_period, branch_no,
  contract_status, paid_installments, remaining_installments, remaining_amount,
  overdue_installments, next_due_date, next_due_amount, last_payment_date,
  pa_refno, pa_product, pa_effective, pa_expired, pa_insured_amount, pa_premium,
  closure_letter_type, closure_tracking, closure_sent_date,
  lockton_policy_no, vehicle_registration, tax_plate_tracking, tax_plate_sent_date,
  mailing_doc_no, mailing_received, guarantor_name
"""

# ──────────────────────────────────────────────────────────────────────
# FEW-SHOT EXAMPLES
# ──────────────────────────────────────────────────────────────────────
FEW_SHOT_EXAMPLES = """
# ตัวอย่างคำถาม → SQL

Q: มีสัญญาทั้งหมดกี่สัญญา
SQL: SELECT COUNT(*) FROM contracts;

Q: ลูกค้าค้างชำระกี่งวด มีใครบ้าง
SQL: SELECT contract_no, customer_name, overdue_installments, remaining_amount
     FROM v_contract_360
     WHERE overdue_installments > 0
     ORDER BY overdue_installments DESC;

Q: สรุปสถานะสัญญาทั้งระบบ
SQL: SELECT contract_status, COUNT(*) AS num
     FROM contract_payment_summary
     GROUP BY contract_status ORDER BY num DESC;

Q: หาลูกค้าชื่อวิชา ผ่อนถึงงวดที่เท่าไหร่
SQL: SELECT contract_no, customer_name, paid_installments, hire_purchase_period
     FROM v_contract_360
     WHERE customer_name ILIKE '%วิชา%';

Q: ค้นหาด้วยเลขบัตรประชาชน 1483103459144
SQL: SELECT contract_no, customer_name, product_type, contract_status
     FROM v_contract_360 v JOIN contracts c USING (contract_no)
     WHERE c.customer_idcard = '1483103459144';

Q: สัญญาเลขที่ 416261100316 งวดต่อไปต้องจ่ายเท่าไหร่ วันไหน
SQL: SELECT contract_no, next_due_date, next_due_amount, remaining_installments
     FROM contract_payment_summary WHERE contract_no = '416261100316';

Q: ลูกค้าที่มีประกัน PA หมดอายุภายใน 6 เดือนนี้
SQL: SELECT customer_name, pa_product, pa_expired,
            (pa_expired - CURRENT_DATE) AS days_left
     FROM v_contract_360
     WHERE pa_expired BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '6 months'
     ORDER BY pa_expired;

Q: สัญญาที่ปิดบัญชีแล้วในเดือนที่ผ่านมา
SQL: SELECT contract_no, customer_name, closure_letter_type, closure_sent_date
     FROM v_contract_360
     WHERE closure_sent_date >= CURRENT_DATE - INTERVAL '30 days';

Q: งวดที่ค้างเกิน 60 วันมีกี่งวด
SQL: SELECT COUNT(*) FROM installment_schedule
     WHERE status = 'OVERDUE' AND due_date < CURRENT_DATE - INTERVAL '60 days';

Q: ค่างวดเฉลี่ยของสัญญา 416261100316
SQL: SELECT ROUND(AVG(installment_amount)::numeric, 2) AS avg_installment
     FROM installment_schedule WHERE contract_no = '416261100316';

Q: ลูกค้าผ่อนค้างที่มี PA insurance ใกล้หมดอายุ
SQL: SELECT customer_name, overdue_installments, remaining_amount,
            pa_product, pa_expired
     FROM v_contract_360
     WHERE overdue_installments > 0
       AND pa_expired IS NOT NULL
       AND pa_expired < CURRENT_DATE + INTERVAL '90 days';

Q: ลูกค้าที่มีสัญญาแต่ยังไม่ได้ซื้อ PA
SQL: SELECT c.contract_no, c.customer_name, c.product_type, c.principal_amount
     FROM contracts c
     LEFT JOIN pa_insurance_policies p ON p.contractno = c.contract_no
     WHERE p.contractno IS NULL;

Q: สัญญาที่ส่งจดหมาย WO (Write-off) แล้ว มีกี่สัญญา
SQL: SELECT COUNT(*) FROM closure_letters WHERE letter_type = 'WO';

Q: สัญญาทั้งหมดที่ยังไม่ปิดบัญชี
SQL: SELECT c.contract_no, c.customer_name FROM contracts c
     WHERE NOT EXISTS (SELECT 1 FROM closure_letters cl WHERE cl.contract_no = c.contract_no);

Q: ลูกค้าที่จ่ายเงินตรงเวลาทุกงวด
SQL: SELECT contract_no, COUNT(*) AS total
     FROM installment_schedule
     GROUP BY contract_no
     HAVING COUNT(*) FILTER (WHERE status = 'OVERDUE') = 0
        AND COUNT(*) FILTER (WHERE status = 'PAID') > 0;
"""

# ──────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT (แก้ตรงนี้เพื่อเปลี่ยน behavior)
# ──────────────────────────────────────────────────────────────────────
def build_system_prompt() -> str:
    lang_instruction = {
        "thai": "ตอบเป็นภาษาไทยเสมอ",
        "english": "Always answer in English",
        "auto": "Match the user's language (ตอบตามภาษาที่ user ถาม)",
    }[OUTPUT_FORMAT["language"]]

    summary_instruction = {
        "none": "ไม่ต้องสรุปอะไรเพิ่ม",
        "bullet": "สรุปคำตอบเป็น bullet points สั้นๆ 2-4 ข้อ",
        "paragraph": "สรุปเป็นย่อหน้าธรรมชาติ 2-3 ประโยค",
    }[OUTPUT_FORMAT["summary"]]

    return f"""คุณเป็น SQL Analyst สำหรับ Next Capital (สถาบันการเงินไทย)
มีหน้าที่แปลงคำถามภาษาไทยเป็น SQL query สำหรับ PostgreSQL บน Supabase

{DB_SCHEMA}

{FEW_SHOT_EXAMPLES}

## กฎสำคัญ
1. **SELECT-only** — ห้ามใช้ INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE
2. ใช้ **v_contract_360** เป็นอันดับแรกถ้าตอบได้ (ลด JOIN complexity)
3. ใช้ **PostgreSQL syntax**: INTERVAL '30 days', ILIKE, ::cast, CURRENT_DATE
4. ค้นชื่อใช้ **ILIKE '%name%'** เสมอ (ไม่ใช่ =) เพราะมีภาษาไทย
5. **pa_insurance_policies.contractno** ไม่มี underscore — ระวังตอน JOIN
6. Enum **UPPERCASE**: 'NORMAL', 'LATE', 'DEFAULT', 'CLOSED', 'PAID', 'PENDING', 'OVERDUE', 'WAIVED'
7. เพิ่ม `LIMIT {OUTPUT_FORMAT['row_limit']}` ทุก query ที่ไม่มี aggregation
8. ถ้าคำถามไม่เกี่ยวกับ database ตอบ: `OUT_OF_SCOPE: <เหตุผลสั้นๆ>`

## รูปแบบคำตอบ (สำคัญ ทำตามให้ครบ)
ตอบเป็น 2 ส่วนเสมอ คั่นด้วย `---`:

ส่วนที่ 1: SQL code ใน code block:
```sql
SELECT ...
```

ส่วนที่ 2: คำอธิบายแบบสรุป
{lang_instruction}
{summary_instruction}
อธิบายว่า query นี้ทำอะไร และผลลัพธ์หมายความว่ายังไง (พูดถึงข้อมูลที่จะได้ ไม่ต้อง execute เอง)

ตัวอย่างคำตอบที่ถูกต้อง:
```sql
SELECT contract_no, customer_name, overdue_installments
FROM v_contract_360
WHERE overdue_installments > 0
ORDER BY overdue_installments DESC
LIMIT 100;
```
---
- ดึงรายการสัญญาที่มีงวดค้างชำระ
- เรียงจากค้างมากไปน้อย
- จำกัด 100 รายการแรก
"""


# ──────────────────────────────────────────────────────────────────────
# PASS 2 PROMPT — สรุปผลลัพธ์จริงจาก DB เป็นคำพูดธรรมชาติ
# (แก้ตรงนี้เพื่อเปลี่ยน "บทพูด" ของบอท)
# ──────────────────────────────────────────────────────────────────────
def build_answer_prompt(user_question: str, sql: str, result_summary: str) -> str:
    """
    Prompt รอบ 2: ให้ LLM อ่านผลลัพธ์จริงจาก DB มาสรุปเป็นคำพูดธรรมชาติ
    เรียกใช้หลังจาก execute SQL แล้วเท่านั้น (มีผลลัพธ์จริงอยู่ในมือ)
    """
    summary_style = {
        "none": "ตอบสั้นๆ ตรงประเด็น ไม่ต้องมีคำถามต่อท้าย",
        "bullet": "ตอบเป็น bullet สั้นๆ 1-2 ข้อ ปิดท้ายด้วยคำถามชวนคุยต่อ",
        "paragraph": "ตอบเป็นประโยคพูดธรรมชาติ เหมือนพนักงานตอบลูกค้า ปิดท้ายด้วยคำถามชวนคุยต่อ",
    }[OUTPUT_FORMAT["summary"]]

    return f"""คุณเป็นผู้ช่วยตอบคำถามของทีม Customer Service ที่ Next Capital
น้ำเสียง: เป็นมิตร สุภาพ กระชับ เหมือนพนักงานคุยกับเพื่อนร่วมงาน

คำถามของผู้ใช้: {user_question}

ผลลัพธ์จริงจากฐานข้อมูล:
{result_summary}

จงสรุปผลลัพธ์นี้เป็นคำพูดธรรมชาติแบบคนพูดกับคน {summary_style}

กฎสำคัญ:
- พูดถึง "ผลลัพธ์ที่ได้จริง" เท่านั้น (ถ้าได้ตัวเลข 8 ให้บอกว่า "มี 8 คน/รายการ")
- ห้ามพูดถึงคำว่า SQL, query, DISTINCT, table, column หรือศัพท์เทคนิคใดๆ
- ห้ามอธิบายว่า "คำนวณยังไง" — บอกแค่ผลลัพธ์ที่ user สนใจ
- ถ้าผลลัพธ์มีหลายแถว ให้สรุปภาพรวมสั้นๆ ก่อน (ไม่ต้องอ่านทุกแถวออกมา เพราะจะมีตารางโชว์ข้างใต้อยู่แล้ว)
- ปิดท้ายด้วยคำถามชวนคุยต่อแบบเป็นธรรมชาติ เช่น "ต้องการรายละเอียดเพิ่มเติมไหมครับ" หรือ "อยากดูรายชื่อทั้งหมดไหมครับ"
- ใช้ภาษาไทยเป็นธรรมชาติ ลงท้ายด้วย ครับ/ค่ะ
- ความยาว 1-3 ประโยคพอ ไม่ต้องยาว

ตัวอย่างคำตอบที่ดี:
"ตอนนี้มีลูกค้าที่ค้างชำระอยู่ 8 คนครับ ต้องการดูรายชื่อทั้งหมดไหมครับ"
"เดือนนี้ปิดบัญชีไปแล้ว 5 สัญญาครับ อยากให้ส่งรายละเอียดเพิ่มไหมครับ"
"เจอลูกค้าชื่อวิชา ผ่อนมาแล้ว 24 จาก 36 งวดครับ เหลืออีกแค่ 12 งวดก็ครบสัญญาแล้ว ต้องการดูรายละเอียดเพิ่มไหมครับ"
"""

# ──────────────────────────────────────────────────────────────────────
# EVENT EXTRACTION PROMPT
# ──────────────────────────────────────────────────────────────────────
def build_event_extraction_prompt() -> str:
    return """คุณคือผู้เชี่ยวชาญด้าน Natural Language Processing (NLP) และ Information Extraction
หน้าที่ของคุณคือการอ่านข้อความ (ภาษาไทยหรืออังกฤษ) แล้วแยกแยะ "เหตุการณ์" (Events) ออกมาเป็น JSON

สำหรับแต่ละเหตุการณ์ ให้ระบุ Thematic Roles ดังนี้:
- Agent (ผู้กระทำ)
- Predicate (กริยา หรือ การกระทำ)
- Theme (สิ่งที่ถูกกระทำ หรือ สิ่งที่เกี่ยวข้อง)

กฎการสกัด:
1. ข้อความหนึ่งอาจมีหลายเหตุการณ์ ให้แยกออกมาเป็นหลายๆ object ใน array
2. หากไม่มี Agent หรือ Theme ที่ชัดเจน ให้ใส่ null หรือละเว้นไว้
3. ผลลัพธ์ต้องเป็น JSON array ล้วนๆ ห้ามมี Markdown block (เช่น ```json) และห้ามมีคำอธิบายอื่นใด

ตัวอย่าง Input: "ลูกค้าโวยวายใส่พนักงาน และขอยกเลิกสัญญาทันที"
ตัวอย่าง Output:
[
  {
    "Agent": "ลูกค้า",
    "Predicate": "โวยวายใส่",
    "Theme": "พนักงาน"
  },
  {
    "Agent": "ลูกค้า",
    "Predicate": "ขอยกเลิก",
    "Theme": "สัญญา"
  }
]

ข้อความที่ต้องการวิเคราะห์:
"""
