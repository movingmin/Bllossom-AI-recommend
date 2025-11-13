# crawling/analyze.py
import json
import logging
from pathlib import Path
from typing import Dict, Any

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)

MODEL_NAME = "snunlp/KR-FinBert-SC"  # 감성 분석용 모델

class FinBertSentiment:
    def __init__(self, model_name: str = MODEL_NAME, device: str | None = None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model.to(self.device)

        # 모델마다 다르지만, 보통 금융 FinBERT는 [neg, neu, pos] 순서를 많이 씀
        self.label_order = ["negative", "neutral", "positive"]

        logger.info(f"Loaded FinBERT model on {self.device}")

    def score_text(self, text: str) -> int:
        """
        텍스트 하나에 대해:
        - FinBERT로 [neg, neu, pos] 확률 계산
        - 최종 감성 점수 -5 ~ 5 정수로 리턴
        """
        if not text:
            return 0

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=256,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits  # [1, num_labels]

        probs = torch.softmax(logits, dim=-1)[0].cpu().tolist()
        neg, neu, pos = probs

        # 간단한 스코어링 방식: (pos - neg) * 5
        raw_score = (pos - neg)  # -1 ~ 1 근사
        int_score = int(round(raw_score * 5))  # -5 ~ 5

        if int_score > 5:
            int_score = 5
        if int_score < -5:
            int_score = -5

        return int_score


def analyze_file(
    crawling_path: Path,
    output_path: Path,
):
    logger.info(f"Loading crawling data from: {crawling_path}")
    with crawling_path.open("r", encoding="utf-8") as f:
        crawling_data: Dict[str, Any] = json.load(f)

    sentiment_model = FinBertSentiment()

    response: Dict[str, Any] = {}

    for company, articles in crawling_data.items():
        logger.info(f"Analyzing sentiment for company: {company}")
        company_news = []
        total_sum = 0

        for item in articles:
            title = item.get("title", "") or ""
            content = item.get("content", "") or ""
            text = (title + " " + content).strip()

            point = sentiment_model.score_text(text)
            total_sum += point

            company_news.append(
                {
                    "title": title,
                    "point": point,
                }
            )

        response[company] = {
            "news": company_news,
            "sum": total_sum,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(response, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved sentiment response to: {output_path}")
