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

st.set_page_config(page_title="Brew & Bean · 고객 피드백", layout="wide")

# ── 전역 스타일
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Noto+Sans+KR:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    background-color: #FBF7F2;
    font-family: 'Noto Sans KR', sans-serif;
    color: #3B2314;
  }
  /* 사이드바 */
  section[data-testid="stSidebar"] {
    background-color: #2C1A0E;
  }
  section[data-testid="stSidebar"] * {
    color: #E8D5B7 !important;
  }
  section[data-testid="stSidebar"] .stRadio label {
    font-size: 15px;
    padding: 6px 0;
  }
  /* 제목 */
  h1 { font-family: 'Playfair Display', serif !important; color: #2C1A0E !important; }
  h2, h3 { font-family: 'Playfair Display', serif !important; color: #4A2C2A !important; }
  /* metric */
  [data-testid="stMetricValue"] { color: #6F4E37 !important; font-size: 2rem !important; font-weight: 700 !important; }
  [data-testid="stMetricLabel"] { color: #9E7B5A !important; font-size: 13px !important; }
  /* divider */
  hr { border-color: #D4B896 !important; }
  /* dataframe */
  [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
  /* multiselect */
  [data-testid="stMultiSelect"] > div { border-color: #C8A96E !important; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    sb = create_client(get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY"))
    res = sb.table("feedback").select("*").execute()
    return pd.DataFrame(res.data)

df = load_data()
complaints = df[df["유형"] == "불만"].copy()

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

# ── 사이드바
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:24px 0 12px;">
      <div style="font-size:32px;">☕</div>
      <div style="font-family:'Playfair Display',serif;font-size:20px;font-weight:700;
                  color:#E8D5B7;letter-spacing:1px;">Brew & Bean</div>
      <div style="font-size:11px;color:#9E7B5A;margin-top:4px;">Customer Feedback</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    page = st.radio("페이지", ["☕  오늘의 요약", "📋  전체 피드백"], label_visibility="collapsed")
    st.divider()
    st.caption(f"전체 {len(df)}건 수집")
    st.caption(f"불만 {len(complaints)}건 미처리")
    st.caption("Supabase · 60초 갱신")

# ════════════════════════════════════════
# 요약 페이지
# ════════════════════════════════════════
if page == "☕  오늘의 요약":
    st.markdown("""
    <div style="padding: 8px 0 4px;">
      <span style="font-family:'Playfair Display',serif;font-size:34px;font-weight:700;color:#2C1A0E;">
        오늘의 피드백 요약
      </span><br>
      <span style="font-size:14px;color:#9E7B5A;">가장 급한 불만을 빠르게 확인하세요</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("미처리 불만", f"{len(complaints)}건")
    c2.metric("오늘 신규 불만", f"{today_count}건")
    c3.metric("개선 요청 포함", f"{len(complaints[complaints['부유형'].astype(str).str.strip() == '요청'])}건")

    st.divider()

    st.markdown("""
    <div style="font-family:'Playfair Display',serif;font-size:22px;font-weight:600;
                color:#4A2C2A;margin-bottom:4px;">가장 급한 불만 TOP 3</div>
    <div style="font-size:12px;color:#9E7B5A;margin-bottom:20px;">
      긴급도 = 별점 점수 + 금전(+5) · 운영 장애(+2) · 시설(+1)
    </div>
    """, unsafe_allow_html=True)

    rank_labels = ["1순위", "2순위", "3순위"]
    border_colors = ["#6F4E37", "#9E7B5A", "#C8A96E"]
    bg_colors     = ["#FFF8F0", "#FBF5EE", "#FAF3E8"]

    for i, row in top3.iterrows():
        star_raw = pd.to_numeric(row["별점"], errors="coerce")
        star_str = "★" * int(star_raw) + "☆" * (5 - int(star_raw)) if pd.notna(star_raw) else "별점 없음"
        score    = int(row["긴급도"])
        badge    = (
            "<span style='background:#C8A96E;color:#2C1A0E;border-radius:20px;"
            "padding:2px 10px;font-size:11px;font-weight:600;margin-left:8px;'>개선 요청 포함</span>"
            if str(row.get("부유형", "")).strip() == "요청" else ""
        )
        st.markdown(f"""
<div style="border-left:5px solid {border_colors[i]};background:{bg_colors[i]};
            border-radius:0 12px 12px 0;padding:18px 22px;margin-bottom:16px;
            box-shadow:0 2px 8px rgba(111,78,55,0.08);">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
    <span style="font-size:12px;font-weight:700;color:{border_colors[i]};
                 text-transform:uppercase;letter-spacing:1px;">{rank_labels[i]}</span>
    <span style="font-size:11px;color:#B09070;">
      긴급도 {score}점 &nbsp;·&nbsp; {row['받은날짜']} &nbsp;·&nbsp; {row['경로']}
    </span>
  </div>
  <p style="font-size:15px;font-weight:500;color:#2C1A0E;margin:0 0 8px;line-height:1.6;">
    "{row['내용']}"
  </p>
  <span style="font-size:13px;color:#C8A96E;">{star_str}</span>{badge}
</div>""", unsafe_allow_html=True)

# ════════════════════════════════════════
# 전체 피드백 페이지
# ════════════════════════════════════════
else:
    st.markdown("""
    <div style="padding: 8px 0 4px;">
      <span style="font-family:'Playfair Display',serif;font-size:34px;font-weight:700;color:#2C1A0E;">
        전체 피드백
      </span><br>
      <span style="font-size:14px;color:#9E7B5A;">수집된 모든 고객 의견을 확인하세요</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    counts = df["유형"].value_counts()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("불만", int(counts.get("불만", 0)))
    m2.metric("요청", int(counts.get("요청", 0)))
    m3.metric("칭찬", int(counts.get("칭찬", 0)))
    m4.metric("문의", int(counts.get("문의", 0)))

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("<div style='font-family:Playfair Display,serif;font-size:18px;font-weight:600;color:#4A2C2A;margin-bottom:8px;'>유형별 건수</div>", unsafe_allow_html=True)
        type_df = counts.reset_index()
        type_df.columns = ["유형", "건수"]
        color_map = {"불만": "#8B4513", "요청": "#C8A96E", "칭찬": "#7A9E6E", "문의": "#7A8FA6"}
        chart = (
            alt.Chart(type_df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("유형:N", sort="-y", axis=alt.Axis(labelFontSize=13, labelColor="#4A2C2A", tickColor="#D4B896", domainColor="#D4B896")),
                y=alt.Y("건수:Q", axis=alt.Axis(tickMinStep=1, labelColor="#9E7B5A", gridColor="#EDE0D0", domainColor="#D4B896")),
                color=alt.Color("유형:N",
                    scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())),
                    legend=None),
                tooltip=["유형", "건수"],
            )
            .properties(height=260, background="#FBF7F2")
            .configure_view(strokeOpacity=0)
        )
        st.altair_chart(chart, use_container_width=True)

    with right:
        st.markdown("<div style='font-family:Playfair Display,serif;font-size:18px;font-weight:600;color:#4A2C2A;margin-bottom:8px;'>감정 분포</div>", unsafe_allow_html=True)
        sent_df = df["감정"].value_counts().reset_index()
        sent_df.columns = ["감정", "건수"]
        sent_color = {"긍정": "#7A9E6E", "부정": "#8B4513", "중립": "#C8A96E"}
        pie = (
            alt.Chart(sent_df)
            .mark_arc(innerRadius=60, outerRadius=105)
            .encode(
                theta=alt.Theta("건수:Q"),
                color=alt.Color("감정:N",
                    scale=alt.Scale(domain=list(sent_color.keys()), range=list(sent_color.values())),
                    legend=alt.Legend(labelColor="#4A2C2A", titleColor="#4A2C2A")),
                tooltip=["감정", "건수"],
            )
            .properties(height=260, background="#FBF7F2")
            .configure_view(strokeOpacity=0)
        )
        st.altair_chart(pie, use_container_width=True)

    st.divider()

    st.markdown("<div style='font-family:Playfair Display,serif;font-size:18px;font-weight:600;color:#4A2C2A;margin-bottom:12px;'>피드백 목록</div>", unsafe_allow_html=True)

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
        lambda x: f"★{int(float(x))}" if pd.notna(x) and str(x).strip() not in ("", "nan") else "-"
    )
    st.dataframe(display, use_container_width=True, hide_index=True)
