-- ──────────────────────────────────────────────────────────────────────
-- รัน SQL นี้ใน Supabase SQL Editor ครั้งเดียวก่อนใช้งาน NextAI v2
-- (Dashboard → SQL Editor → New query → paste → Run)
-- ──────────────────────────────────────────────────────────────────────

-- สร้าง RPC function ที่รับ SQL string แล้ว return ผลเป็น JSON
-- ใช้ SECURITY INVOKER (รัน sql ด้วย permission ของผู้เรียก = anon role)
-- เพื่อให้ Postgres ปฏิเสธคำสั่งที่ anon ทำไม่ได้โดยอัตโนมัติ
CREATE OR REPLACE FUNCTION execute_readonly_sql(query_text TEXT)
RETURNS JSON
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
DECLARE
    result JSON;
    upper_q TEXT;
BEGIN
    upper_q := upper(trim(query_text));

    -- Block dangerous keywords (defense in depth — already blocked in Python)
    IF upper_q ~ '\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|MERGE|COPY)\b' THEN
        RAISE EXCEPTION 'Forbidden SQL keyword detected';
    END IF;

    IF NOT (upper_q LIKE 'SELECT%' OR upper_q LIKE 'WITH%') THEN
        RAISE EXCEPTION 'Only SELECT/WITH queries are allowed';
    END IF;

    EXECUTE format('SELECT json_agg(t) FROM (%s) t', query_text) INTO result;
    RETURN COALESCE(result, '[]'::json);
END;
$$;

-- อนุญาตให้ role anon เรียกใช้ function นี้ได้
GRANT EXECUTE ON FUNCTION execute_readonly_sql(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION execute_readonly_sql(TEXT) TO authenticated;

-- (Optional แต่แนะนำ) ให้ anon role อ่านทุกตารางและ view ใน public schema
-- ถ้าเปิด RLS แล้ว ต้องเพิ่ม policy แทน
GRANT USAGE ON SCHEMA public TO anon;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;

-- ทดสอบ:
-- SELECT execute_readonly_sql('SELECT COUNT(*) FROM contracts');
