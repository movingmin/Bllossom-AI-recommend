import json
from pathlib import Path

from transformers import pipeline

# ---- 경로 설정 ----
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
INPUT_PATH = DB_DIR / "crawling.json"
COMPANY_SCORE_PATH = DB_DIR / "company_scores.json"  # 기업별 점수 저장
LABELED_DIR = DB_DIR / "labeled"                     # 회사별 라벨링 파일들 모아둘 디렉터리. 2000개만드는건좀부담스러워서안쓸듯


MODEL_NAME = "snunlp/KR-FinBert-SC"


def load_classifier():
    """
    KR-FinBERT 분류 파이프라인 로딩
    device = -1  → CPU 사용, 0이면 GPU 사용
    """
    device = -1  # GPU 쓰려면 0으로 변경 (지금은 CPU)
    clf = pipeline(
        task="text-classification",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        device=device,
        truncation=True,
        max_length=512,
    )
    return clf


def make_input_text(title: str, content: str) -> str:
    """
    제목 + 본문을 하나의 텍스트로 합치기
    """
    title = (title or "").strip()
    content = (content or "").strip()
    if not content:
        return title
    return f"[제목] {title}\n[본문] {content}"


def label_to_point(label: str | None) -> int:
    """
    모델이 준 label을 -1 / 0 / +1 점수로 변환
    """
    if not label:
        return 0
    l = label.lower()
    if l == "positive":
        return 1
    if l == "negative":
        return -1
    return 0  # neutral or 기타


def sanitize_filename(name: str) -> str:
    """
    회사 이름을 파일명에 쓸 수 있게 안전하게 변환
    (슬래시, 공백 등 제거)
    """
    invalid_chars = r'\/:*?"<>|'
    safe = "".join(ch for ch in name if ch not in invalid_chars)
    safe = safe.replace(" ", "_")
    if not safe:
        safe = "unknown_company"
    return safe


def main():
    # 디렉터리 준비
    LABELED_DIR.mkdir(parents=True, exist_ok=True)

    # 1) 원본 크롤링 데이터 로드
    print(f"Loading crawling data from: {INPUT_PATH}")
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # 2) 모델 로드
    print("Loading KR-FinBERT model...")
    classifier = load_classifier()
    print("Model loaded.")

    company_scores: dict[str, dict] = {}

    # 3) 회사별로 기사 라벨링 + 회사별 JSON 파일로 저장
    for company_name, articles in data.items():
        print(f"Labeling articles for company: {company_name} (count={len(articles)})")

        labeled_articles = []

        # 기업별 카운터
        pos_count = 0
        neg_count = 0
        neu_count = 0

        for article in articles:
            title = article.get("title", "")
            content = article.get("content", "")
            text = make_input_text(title, content)

            try:
                result = classifier(text)[0]
                label = result.get("label")
                confidence = float(result.get("score", 0.0))
            except Exception as e:
                print(f"[WARN] Failed to classify article '{title}': {e}")
                label = None
                confidence = 0.0

            # -1 / 0 / +1 점수
            sentiment_point = label_to_point(label)

            # 기업별 카운트
            if label:
                l = label.lower()
                if l == "positive":
                    pos_count += 1
                elif l == "negative":
                    neg_count += 1
                else:
                    neu_count += 1

            # 기사 하나에 라벨 정보 추가
            article_with_label = {
                **article,
                "sentiment_label": label,            # 'positive' / 'negative' / 'neutral'
                "sentiment_confidence": confidence,  # 0.0 ~ 1.0 (모델 확신도)
                "sentiment_point": sentiment_point,  # -1 / 0 / +1 (우리 점수)
            }
            labeled_articles.append(article_with_label)

        # ----- 회사별 라벨링 결과를 개별 파일로 저장 (db/labeled/ 아래) -----
        # safe_name = sanitize_filename(company_name)
        # company_output_path = LABELED_DIR / f"crawling_labeled_{safe_name}.json"
        # with company_output_path.open("w", encoding="utf-8") as f:
        #     json.dump(labeled_articles, f, ensure_ascii=False, indent=2)
        # print(f"Saved labeled articles for '{company_name}' to: {company_output_path}")

        # ----- 회사별 점수 집계 -----
        company_score = pos_count - neg_count
        company_scores[company_name] = {
            "positive_count": pos_count,
            "negative_count": neg_count,
            "neutral_count": neu_count,
            "total_articles": len(labeled_articles),
            "company_score": company_score,
        }

        print(
            f"[SUMMARY] {company_name}: "
            f"+{pos_count} / -{neg_count} / 0:{neu_count} "
            f"→ company_score = {company_score}"
        )

    # 4) 기업별 점수 결과 저장 (핵심 파일)
    with COMPANY_SCORE_PATH.open("w", encoding="utf-8") as f:
        json.dump(company_scores, f, ensure_ascii=False, indent=2)
    print(f"Saved company scores to: {COMPANY_SCORE_PATH}")


if __name__ == "__main__":
    main()
