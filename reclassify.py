"""
새 우선순위 규칙으로 피드백을 재분류하고 부유형 컬럼을 추가한다.

Priority 1 → 불만 : 별점 1~2  OR  부정 감정 키워드 포함
Priority 2 → 요청 : 요청 표현 포함 (Priority 1 미해당 시)
Priority 3 → 칭찬 : 긍정 표현
Priority 4 → 문의 : 질문형
"""
import math
import pandas as pd

CSV_PATH = "Day3_과제_feedback_분류.csv"

NEGATIVE_KEYWORDS = [
    "너무 달아", "오래 걸려", "좁아요", "식었어요", "불만", "끊겨요",
    "불편", "안 쌓", "부담", "잘못 받", "올랐네요", "오류", "잘못",
]
REQUEST_KEYWORDS  = ["확인", "하면 좋겠", "됐으면", "해주세요", "있으면 좋겠", "주세요"]
POSITIVE_KEYWORDS = ["좋아요", "감사해요", "추천", "맛있어요", "예뻐", "단골", "퀄리티", "완벽"]


def is_low_star(val) -> bool:
    v = pd.to_numeric(val, errors="coerce")
    return pd.notna(v) and v <= 2


def has_any(text: str, keywords: list) -> bool:
    return any(k in text for k in keywords)


def classify(row) -> tuple[str, str | None]:
    """(주유형, 부유형) 반환. 부유형 없으면 None."""
    text  = str(row["내용"])
    star  = row["별점"]
    is_complaint  = is_low_star(star) or has_any(text, NEGATIVE_KEYWORDS)
    is_request    = has_any(text, REQUEST_KEYWORDS)
    is_praise     = has_any(text, POSITIVE_KEYWORDS)
    is_inquiry    = "?" in text or any(
                        text.endswith(s) for s in ["나요.", "되나요.", "되나요?", "나요?", "건가요.", "건가요?"]
                    )

    if is_complaint:
        sub = "요청" if is_request else None
        return "불만", sub

    if is_request:
        return "요청", None

    if is_praise:
        return "칭찬", None

    if is_inquiry:
        return "문의", None

    # 기존 분류 유지 (규칙 미해당)
    return row["유형"], None


def main():
    df = pd.read_csv(CSV_PATH)
    changes = []

    results = df.apply(classify, axis=1)
    df["유형_new"]  = results.apply(lambda x: x[0])
    df["부유형"]    = results.apply(lambda x: x[1] if x[1] else "")

    for _, row in df.iterrows():
        if row["유형"] != row["유형_new"]:
            changes.append(
                f"  id {int(row['id'])}: {row['유형']} → {row['유형_new']}"
                + (f"  (부유형: {row['부유형']})" if row['부유형'] else "")
            )

    df["유형"] = df["유형_new"]
    df = df.drop(columns=["유형_new"])

    df.to_csv(CSV_PATH, index=False)

    if changes:
        print(f"재분류 완료 - {len(changes)}건 변경:")
        for c in changes:
            print(c)
    else:
        print("재분류 완료 - 변경 없음 (모든 행이 새 규칙과 일치)")


if __name__ == "__main__":
    main()
