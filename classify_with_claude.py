"""
Claude API(claude-haiku-4-5)로 피드백을 분류한다.
Few-shot 예시 3개로 기준을 고정하고, 각 피드백에 유형·감정·부유형을 부여한다.

실행: python classify_with_claude.py
결과: Day3_과제_feedback_분류.csv 덮어쓰기
"""
import os, json, time
import pandas as pd
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── 시스템 프롬프트: 규칙 + Few-shot 예시 ──────────────────────────────────
SYSTEM = """
당신은 카페 고객 피드백 분류 전문가입니다.
각 피드백을 읽고 아래 규칙에 따라 JSON으로만 응답하세요. 다른 텍스트는 절대 출력하지 마세요.

## 분류 우선순위 (유형)
1. 불만: 별점 1~2점이거나 부정적 감정 표현이 있을 때 (다른 요소보다 우선)
2. 요청: "~하면 좋겠다", "확인해달라", "해주세요" 등 개선·추가 요청 (불만 아닐 때)
3. 칭찬: 긍정적 감상, 감사 표현
4. 문의: 사실 확인을 위한 질문

## 부유형
불만이면서 동시에 요청 표현이 있으면 부유형을 "요청"으로 설정. 없으면 null.

## 감정
- 긍정: 만족·칭찬·감사
- 부정: 불만·실망·불편
- 중립: 단순 질문·중립적 요청

## 응답 형식 (JSON만, 설명 없이)
{"유형": "불만|요청|칭찬|문의", "감정": "긍정|부정|중립", "부유형": "요청|null"}

## Few-shot 예시

입력: 별점=1, 내용="주문하고 20분 기다렸어요. 너무 오래 걸려요."
출력: {"유형": "불만", "감정": "부정", "부유형": null}

입력: 별점=2, 내용="신메뉴 라떼 시켰는데 너무 달아요. 당도 조절 옵션 있으면 좋겠어요."
출력: {"유형": "불만", "감정": "부정", "부유형": "요청"}

입력: 별점=없음, 내용="비건 디저트도 있나요? 우유 알레르기가 있어서요."
출력: {"유형": "문의", "감정": "중립", "부유형": null}
""".strip()


def classify_one(star, content: str) -> dict:
    star_str = str(int(star)) if pd.notna(star) and str(star).strip() not in ("", "nan") else "없음"
    user_msg = f"입력: 별점={star_str}, 내용=\"{content}\""

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = resp.content[0].text.strip()
    result = json.loads(raw)
    # null 문자열 정규화
    if result.get("부유형") in (None, "null", ""):
        result["부유형"] = ""
    return result


def main():
    df = pd.read_csv("Day3_과제_feedback_분류.csv")

    # 원본 열만 남기고 재분류
    keep_cols = ["id", "받은날짜", "경로", "별점", "내용"]
    base = df[keep_cols].copy()

    types, sentiments, subtypes = [], [], []

    for _, row in base.iterrows():
        result = classify_one(row["별점"], row["내용"])
        types.append(result["유형"])
        sentiments.append(result["감정"])
        subtypes.append(result.get("부유형", ""))
        print(f"  id {int(row['id'])}: {result['유형']} / {result['감정']}"
              + (f" / 부유형={result['부유형']}" if result.get("부유형") else ""))
        time.sleep(0.2)  # rate limit 여유

    base["유형"]  = types
    base["감정"]  = sentiments
    base["부유형"] = subtypes

    base.to_csv("Day3_과제_feedback_분류.csv", index=False)
    print(f"\n분류 완료 - {len(base)}건 저장 완료")


if __name__ == "__main__":
    main()
