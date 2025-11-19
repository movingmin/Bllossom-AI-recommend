import requests
from .sentiment import format_sentiment_summary

OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "bllossom-3b-kor"


def ask_invest_ai(question: str, stock_name: str | None = None) -> str:
    sentiment_text = None
    if stock_name:
        sentiment_text = format_sentiment_summary(stock_name)

    system_prompt = (
        "너는 'AI 주식 투자 시뮬레이터' 서비스의 한국 주식 투자 상담 AI다.\n"
        "- 수익률 보장 금지, 리스크/장단점 항상 설명.\n"
        "- 아래 [뉴스 분석 요약]이 있으면 반드시 참고해서 의견을 말해라.\n"
    )

    if sentiment_text:
        system_prompt += f"\n[뉴스 분석 요약]\n{sentiment_text}\n[요약 끝]\n"

    payload = {
        "model": MODEL_NAME,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "options": {
            "temperature": 0.3,
            "num_predict": 256,
        },
    }

    try:
        resp = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"AI 서버 오류: {e}"
