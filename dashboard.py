import os
import streamlit as st
import pandas as pd
import altair as alt
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

st.set_page_config(page_title="피드백 대시보드", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    sb = create_client(get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY"))
    res = sb.table("feedback").select("*").execute()
    return pd.DataFrame(res.data)

df = load_data()
complaints = df[df["유형"] == "불만"].copy()

# ── 긴급도 계산
def star_score(val):
    v = pd.to_numeric(val, errors="coerce")
    return (6 - v) if pd.notna(v) else 3

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

today = str(date.today())
today_count = len(complaints[complaints["받은날짜"] == today])
top3 = complaints.sort_values("긴급도", ascending=False).head(3).reset_index(drop=True)

# ── 사이드바 네비게이션
page = st.sidebar.radio("페이지", ["요약", "전체 보기"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption(f"총 {len(df)}건 · 불만 {len(complaints)}건")
st.sidebar.caption("Supabase 실시간 연동 · 60초 캐시")

# ════════════════════════════════════════
# 요약 페이지
# ════════════════════════════════════════
if page == "요약":
    st.title("급한 불만 모니터링")

    c1, c2, c3 = st.columns(3)
    c1.metric("미처리 불만", f"{len(complaints)}건")
    c2.metric("오늘 신규 불만", f"{today_count}건")
    c3.metric("개선 요청 포함", f"{len(complaints[complaints['부유형'].astype(str).str.strip() == '요청'])}건")

    st.divider()

    st.subheader("가장 급한 불만 TOP 3")
    st.caption("긴급도 = 별점 점수 + 금전 가중치(+5) · 운영 장애(+2) · 시설(+1)")

    rank_label  = ["1순위", "2순위", "3순위"]
    border_colors = ["#D32F2F", "#E64A19", "#F57C00"]

    for i, row in top3.iterrows():
        star_raw = pd.to_numeric(row["별점"], errors="coerce")
        star_str = "⭐" * int(star_raw) if pd.notna(star_raw) else "별점 없음"
        score    = int(row["긴급도"])
        badge    = ("&nbsp;&nbsp;<span style='background:#FFF3E0;color:#E65100;"
                    "border-radius:4px;padding:2px 8px;font-size:12px;font-weight:600;'>"
                    "개선 요청 포함</span>"
                    if str(row.get("부유형", "")).strip() == "요청" else "")

        st.markdown(f"""
<div style="border-left:6px solid {border_colors[i]};background:#FFFAF9;
            border-radius:8px;padding:16px 20px;margin-bottom:14px;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:13px;font-weight:700;color:{border_colors[i]};">{rank_label[i]}</span>
    <span style="font-size:12px;color:#999;">긴급도 {score}점 &nbsp;|&nbsp; {row['받은날짜']} · {row['경로']}</span>
  </div>
  <p style="font-size:16px;font-weight:600;margin:8px 0 4px;">{row['내용']}</p>
  <span style="font-size:13px;color:#888;">{star_str}</span>{badge}
</div>""", unsafe_allow_html=True)

# ════════════════════════════════════════
# 전체 보기 페이지
# ════════════════════════════════════════
else:
    st.title("전체 피드백")

    # ── 지표 4개
    counts = df["유형"].value_counts()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("불만", int(counts.get("불만", 0)))
    m2.metric("요청", int(counts.get("요청", 0)))
    m3.metric("칭찬", int(counts.get("칭찬", 0)))
    m4.metric("문의", int(counts.get("문의", 0)))

    st.divider()

    # ── 차트 2개
    left, right = st.columns(2)

    with left:
        st.subheader("유형별 건수")
        type_df = counts.reset_index()
        type_df.columns = ["유형", "건수"]
        color_map = {"불만": "#EF5350", "요청": "#FFA726", "칭찬": "#66BB6A", "문의": "#42A5F5"}
        chart = (
            alt.Chart(type_df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("유형:N", sort="-y", axis=alt.Axis(labelFontSize=13)),
                y=alt.Y("건수:Q", axis=alt.Axis(tickMinStep=1)),
                color=alt.Color("유형:N",
                    scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())),
                    legend=None),
                tooltip=["유형", "건수"],
            ).properties(height=260)
        )
        st.altair_chart(chart, use_container_width=True)

    with right:
        st.subheader("감정 분포")
        sent_df = df["감정"].value_counts().reset_index()
        sent_df.columns = ["감정", "건수"]
        sent_color = {"긍정": "#66BB6A", "부정": "#EF5350", "중립": "#90A4AE"}
        pie = (
            alt.Chart(sent_df)
            .mark_arc(innerRadius=55, outerRadius=100)
            .encode(
                theta=alt.Theta("건수:Q"),
                color=alt.Color("감정:N",
                    scale=alt.Scale(domain=list(sent_color.keys()), range=list(sent_color.values()))),
                tooltip=["감정", "건수"],
            ).properties(height=260)
        )
        st.altair_chart(pie, use_container_width=True)

    st.divider()

    # ── 필터 + 테이블
    st.subheader("피드백 목록")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_type = st.multiselect("유형 필터", ["불만", "요청", "칭찬", "문의"],
                                     default=["불만", "요청", "칭찬", "문의"])
    with col_f2:
        filter_sent = st.multiselect("감정 필터", ["긍정", "부정", "중립"],
                                     default=["긍정", "부정", "중립"])

    filtered = df[df["유형"].isin(filter_type) & df["감정"].isin(filter_sent)]
    display = filtered[["id", "받은날짜", "경로", "별점", "유형", "감정", "부유형", "내용"]].copy()
    display["별점"] = display["별점"].apply(
        lambda x: f"⭐{int(float(x))}" if pd.notna(x) and str(x).strip() not in ("", "nan") else "-"
    )
    st.dataframe(display, use_container_width=True, hide_index=True)
