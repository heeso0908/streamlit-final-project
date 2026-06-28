"""
CSV 데이터를 Supabase feedback 테이블에 업로드하는 스크립트.
테이블이 없으면 안내 메시지를 출력합니다.
"""
import os
import math
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supabase = create_client(url, key)

TABLE = "feedback"
CSV_PATH = "Day3_과제_feedback_분류.csv"

df = pd.read_csv(CSV_PATH)

# 별점 컬럼: NaN → None (JSON null)
def clean(val):
    if isinstance(val, float):
        if math.isnan(val):
            return None
        return int(val)
    return val

rows = [
    {
        "id":       int(r["id"]),
        "받은날짜":  r["받은날짜"],
        "경로":     r["경로"],
        "별점":     clean(r["별점"]),
        "내용":     r["내용"],
        "유형":     r["유형"],
        "감정":     r["감정"],
        "부유형":   r["부유형"] if pd.notna(r.get("부유형")) and str(r.get("부유형", "")).strip() else None,
    }
    for _, r in df.iterrows()
]

try:
    # upsert: id 기준으로 중복 방지
    res = supabase.table(TABLE).upsert(rows, on_conflict="id").execute()
    print(f"업로드 완료: {len(rows)}건 → Supabase '{TABLE}' 테이블")
except Exception as e:
    msg = str(e)
    if "does not exist" in msg or "42P01" in msg:
        print(
            "[오류] 테이블이 없습니다. Supabase 대시보드 > SQL Editor에서 아래 SQL을 먼저 실행해 주세요.\n"
        )
        print(CREATE_SQL)
    else:
        raise

CREATE_SQL = """
create table feedback (
  id       int primary key,
  받은날짜  text,
  경로     text,
  별점     int,
  내용     text,
  유형     text,
  감정     text
);
"""
