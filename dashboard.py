import os
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key)

st.set_page_config(page_title="불만 모니터링", layout="centered")

@st.cache_data(ttl=60)
def load_data():
    sb = create_client(get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY"))
    res = sb.table("feedback").select("*").execute()
    return pd.DataFrame(res.data)

df = load_data()
complaints = df[df["유형"] == "불만"].copy()

# ── 긴급도 점수 계산
# 별점: 낮을수록 높은 점수 (1점→5점, 없음→3점)
def star_score(val):
    v = pd.to_numeric(val, errors="coerce")
    return (6 - v) if pd.notna(v) else 3

# 카테고리 가중치: 금전 직결 여부 우선
# 금전(+5) > 운영 장애(+2) > 서비스·시설(+1)
WEIGHTS = [
    (["결제", "포인트", "환불", "가격", "금액", "할인", "비용", "요금"], 5),
    (["앱", "오류", "기프티콘", "기다", "직원", "잘못"], 2),
    (["와이파이", "자리", "화장실", "진동벨"], 1),
]

def category_weight(text):
    for keywords, w in WEIGHTS:
        if any(k in text for k in keywords):
            return w
    return 0

complaints["긴급도"] = (
    complaints["별점"].apply(star_score)
    + complaints["내용"].apply(category_weight)
)

# ── 미처리 건수 (전체 불만 = 미처리로 간주)
total_complaints = len(complaints)

# ── 오늘 신규 불만
today = str(date.today())
today_complaints = complaints[complaints["받은날짜"] == today]
today_count = len(today_complaints)

# ── TOP 3
top3 = complaints.sort_values("긴급도", ascending=False).head(3).reset_index(drop=True)

# ════════════════════════════════════
# 화면
# ════════════════════════════════════
st.title("급한 불만 모니터링")

# 지표 2개만
c1, c2 = st.columns(2)
c1.metric("미처리 불만", f"{total_complaints}건")
c2.metric("오늘 신규 불만", f"{today_count}건")

st.divider()

# TOP 3 카드
st.subheader("가장 급한 불만 TOP 3")
st.caption("긴급도 = 별점 점수 + 금전 이슈 가중치 (결제·포인트·환불·가격 +5, 운영 장애 +2, 시설 +1)")

rank_label = ["1순위", "2순위", "3순위"]
border_colors = ["#D32F2F", "#E64A19", "#F57C00"]

for i, row in top3.iterrows():
    star_raw = pd.to_numeric(row["별점"], errors="coerce")
    star_str = "⭐" * int(star_raw) if pd.notna(star_raw) else "별점 없음"
    score = int(row["긴급도"])

    st.markdown(
        f"""
<div style="border-left:6px solid {border_colors[i]};
            background:#FFFAF9;border-radius:8px;
            padding:16px 20px;margin-bottom:14px;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:13px;font-weight:700;color:{border_colors[i]};">
      {rank_label[i]}
    </span>
    <span style="font-size:12px;color:#999;">
      긴급도 {score}점 &nbsp;|&nbsp; {row['받은날짜']} · {row['경로']}
    </span>
  </div>
  <p style="font-size:16px;font-weight:600;margin:8px 0 4px;">{row['내용']}</p>
  <span style="font-size:13px;color:#888;">{star_str}</span>
  {"&nbsp;&nbsp;<span style='background:#FFF3E0;color:#E65100;border-radius:4px;padding:2px 8px;font-size:12px;font-weight:600;'>개선 요청 포함</span>" if str(row.get("부유형","")).strip() == "요청" else ""}
</div>
""",
        unsafe_allow_html=True,
    )
