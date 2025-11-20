import json
from pathlib import Path

# recommend 폴더 기준
BASE_DIR = Path(__file__).resolve().parent.parent

# 윈도우에서 확장자 숨겨져서 'company_scores'로 보이더라도
# 실제 파일명은 company_scores.json 인 경우가 많음
DATA_PATH = BASE_DIR / "data" / "company_scores.json"

try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        COMPANY_SCORES = json.load(f)
    print(f"[sentiment] 회사 점수 {len(COMPANY_SCORES)}개 로드 완료")
except FileNotFoundError:
    print(f"[sentiment] 파일을 찾을 수 없습니다: {DATA_PATH}")
    COMPANY_SCORES = {}
except Exception as e:
    print(f"[sentiment] JSON 로딩 중 오류: {e}")
    COMPANY_SCORES = {}


def get_company_score(name: str):
    """
    회사 이름으로 점수 데이터 가져오기. 없으면 None.
    """
    return COMPANY_SCORES.get(name)


def format_sentiment_summary(name: str) -> str | None:
    """
    LLM 프롬프트에 넣을 한 줄 요약 텍스트.
    """
    info = get_company_score(name)
    if not info:
        return None

    pos = info.get("positive_count", 0)
    neg = info.get("negative_count", 0)
    neu = info.get("neutral_count", 0)
    total = info.get("total_articles", 0)
    score = info.get("company_score", 0)

    if score >= 10:
        label = "강한 호재 우세"
    elif score >= 5:
        label = "호재 우세"
    elif score <= -10:
        label = "강한 악재 우세"
    elif score <= -5:
        label = "악재 우세"
    else:
        label = "대체로 중립"

    return (
        f"{name} 관련 최근 기사 {total}개 분석 결과: "
        f"호재 {pos}개, 악재 {neg}개, 중립 {neu}개이며 "
        f"종합 점수는 {score}점으로 '{label}' 상태입니다."
    )
