import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

st.set_page_config(page_title="고객 피드백 대시보드", layout="wide", page_icon="☕")

# ── 데이터 ──────────────────────────────────────────────────────────────────
records = [
    (1,  "2026-05-02", "앱리뷰",   2,    "신메뉴 라떼 시켰는데 너무 달아요. 당도 조절 옵션 있으면 좋겠어요.", "요청"),
    (2,  "2026-05-03", "설문",     None, "매장이 항상 깨끗해서 좋아요. 직원분들도 친절하세요.",            "칭찬"),
    (3,  "2026-05-04", "전화메모", None, "기프티콘 쓰려는데 앱에서 자꾸 오류나요. 확인 부탁드려요.",       "불만"),
    (4,  "2026-05-05", "앱리뷰",   5,    "여기 아메리카노 진짜 맛있어요. 완전 단골 됐어요!",               "칭찬"),
    (5,  "2026-05-06", "인스타DM", None, "비건 디저트도 있나요? 우유 알레르기가 있어서요.",                "문의"),
    (6,  "2026-05-07", "설문",     1,    "주문하고 20분 기다렸어요. 너무 오래 걸려요.",                    "불만"),
    (7,  "2026-05-08", "앱리뷰",   3,    "음료는 괜찮은데 자리가 너무 좁아요.",                           "불만"),
    (8,  "2026-05-09", "전화메모", None, "진동벨이 안 울려서 음료가 다 식었어요. 불만입니다.",             "불만"),
    (9,  "2026-05-10", "설문",     4,    "시즌 한정 메뉴 자주 나왔으면 좋겠어요.",                        "요청"),
    (10, "2026-05-11", "앱리뷰",   2,    "와이파이가 자꾸 끊겨요. 카공하기 불편해요.",                    "불만"),
    (11, "2026-05-12", "인스타DM", None, "단체 예약도 가능한가요? 10명 정도 인원이에요.",                  "문의"),
    (12, "2026-05-13", "설문",     5,    "강아지 동반 가능하게 해주셔서 감사해요!",                        "칭찬"),
    (13, "2026-05-14", "앱리뷰",   1,    "결제는 됐는데 포인트가 안 쌓였어요. 환불해주세요.",              "불만"),
    (14, "2026-05-15", "전화메모", None, "개인 텀블러 가져가면 할인 되나요? 다른 매장은 된다던데.",         "문의"),
    (15, "2026-05-16", "설문",     3,    "화장실이 멀고 찾기 어려워요. 안내 표시가 있으면 좋겠어요.",      "요청"),
    (16, "2026-05-17", "앱리뷰",   5,    "케이크 퀄리티가 베이커리급이에요. 강력 추천!",                   "칭찬"),
    (17, "2026-05-18", "인스타DM", None, "영업시간이 어떻게 되나요? 주말에도 여나요?",                     "문의"),
    (18, "2026-05-19", "설문",     2,    "가격이 좀 올랐네요. 부담스러워요.",                              "불만"),
    (19, "2026-05-20", "앱리뷰",   4,    "콘센트 자리가 많아서 좋아요. 조금만 더 있으면 완벽해요.",        "칭찬"),
    (20, "2026-05-21", "전화메모", None, "두고 간 우산 찾으러 가도 될까요?",                               "문의"),
    (21, "2026-05-22", "설문",     1,    "직원이 주문을 잘못 받았어요. 그것도 두 번이나요.",               "불만"),
    (22, "2026-05-23", "앱리뷰",   5,    "라떼아트가 너무 예뻐서 인스타에 올렸어요.",                      "칭찬"),
]

df = pd.DataFrame(records, columns=["id", "받은날짜", "경로", "별점", "내용", "유형"])

# 가장 급한 불만 top3: 별점1 우선, 그 다음 별점없음, 금전·반복 피해 순
complaints = df[df["유형"] == "불만"].copy()
priority_ids = [13, 21, 6]   # 환불요구 > 반복주문오류 > 장시간대기
top3 = df[df["id"].isin(priority_ids)].set_index("id").loc[priority_ids].reset_index()

# ── 한글 폰트 ────────────────────────────────────────────────────────────────
_font_candidates = [
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/NanumGothic.ttf",
]
_font_path = next((p for p in _font_candidates if os.path.exists(p)), None)
if _font_path:
    _fp = fm.FontProperties(fname=_font_path)
    plt.rcParams["font.family"] = _fp.get_name()
else:
    _fp = fm.FontProperties()
plt.rcParams["axes.unicode_minus"] = False

TYPE_COLOR = {"불만": "#EF5350", "요청": "#FF9800", "칭찬": "#66BB6A", "문의": "#42A5F5"}
TYPE_ICON  = {"불만": "🔴", "요청": "🟠", "칭찬": "🟢", "문의": "🔵"}

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.title("☕ 고객 피드백 대시보드")
st.caption("분석 기간: 2026-05-02 ~ 2026-05-23 · 총 22건")
st.divider()

# ── 지표 카드 ─────────────────────────────────────────────────────────────────
type_counts = df["유형"].value_counts()
avg_rating  = df["별점"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📋 총 피드백",  len(df))
c2.metric("🔴 불만",       type_counts.get("불만", 0))
c3.metric("🟢 칭찬",       type_counts.get("칭찬", 0))
c4.metric("🟠 요청",       type_counts.get("요청", 0))
c5.metric("🔵 문의",       type_counts.get("문의", 0))

st.divider()

# ── 차트 + Top3 ───────────────────────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("유형별 분포")

    ordered = ["불만", "칭찬", "문의", "요청"]
    counts  = [type_counts.get(t, 0) for t in ordered]
    colors  = [TYPE_COLOR[t] for t in ordered]

    fig, ax = plt.subplots(figsize=(5, 3.6))
    bars = ax.bar(ordered, counts, color=colors, width=0.5, edgecolor="white", linewidth=1.5)
    for bar, v in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                str(v), ha="center", va="bottom", fontsize=13, fontweight="bold",
                fontproperties=_fp)
    ax.set_ylim(0, max(counts) + 1.5)
    ax.set_ylabel("건수", fontproperties=_fp)
    ax.set_xticklabels(ordered, fontproperties=_fp, fontsize=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    fig.tight_layout()
    st.pyplot(fig)

    # 평균 별점
    st.markdown(
        f"<div style='text-align:center;font-size:1.05rem;margin-top:4px'>"
        f"⭐ 별점 평균 <b>{avg_rating:.1f}</b> / 5.0"
        f"</div>",
        unsafe_allow_html=True,
    )

with right:
    st.subheader("🚨 가장 급한 불만 Top 3")
    urgency_meta = [
        ("🥇", "#EF5350", "금전 피해 — 결제 후 포인트 미적립, 환불 요구"),
        ("🥈", "#FF7043", "반복 서비스 실패 — 주문 오류 2회 연속"),
        ("🥉", "#FF9800", "운영 문제 — 주문 후 20분 대기"),
    ]
    for (medal, color, reason), (_, row) in zip(urgency_meta, top3.iterrows()):
        star_str = f"⭐{int(row['별점'])}" if pd.notna(row["별점"]) else "별점 없음"
        st.markdown(
            f"""
            <div style="
                background:{color}18;
                border-left:5px solid {color};
                border-radius:6px;
                padding:12px 16px;
                margin-bottom:12px;
            ">
                <span style="font-size:1.2rem">{medal}</span>
                <b style="font-size:1rem"> ID {int(row['id'])} · {star_str} · {row['경로']}</b>
                <br>
                <span style="color:#555;font-size:0.82rem">{reason}</span>
                <br>
                <span style="font-size:0.95rem">{row['내용']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── 전체 피드백 테이블 ────────────────────────────────────────────────────────
st.subheader("전체 피드백 목록")

filter_col, _ = st.columns([1, 3])
selected = filter_col.multiselect(
    "유형 필터",
    options=["불만", "칭찬", "요청", "문의"],
    default=["불만", "칭찬", "요청", "문의"],
)

df_view = df[df["유형"].isin(selected)].copy()
df_view["유형"] = df_view["유형"].map(lambda x: f"{TYPE_ICON.get(x,'')} {x}")
df_view["별점"] = df_view["별점"].apply(
    lambda x: "⭐" * int(x) if pd.notna(x) else "-"
)
st.dataframe(
    df_view[["id", "받은날짜", "경로", "별점", "유형", "내용"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "id":    st.column_config.NumberColumn("ID", width=50),
        "받은날짜": st.column_config.TextColumn("날짜", width=110),
        "경로":  st.column_config.TextColumn("경로", width=90),
        "별점":  st.column_config.TextColumn("별점", width=90),
        "유형":  st.column_config.TextColumn("유형", width=80),
        "내용":  st.column_config.TextColumn("내용", width=500),
    },
)
