# recommend/services/llm.py
from .sentiment import format_sentiment_summary
from .local_llm import generate_response

def ask_invest_ai(question: str, stock_name: str | None = None) -> str:
    """
    question: 사용자가 입력한 질문
    stock_name: 현재 선택된 종목명 (예: '삼성전자')
    """

    sentiment_text = None
    if stock_name:
        sentiment_text = format_sentiment_summary(stock_name)

    system_prompt = (
        "너는 'AI 주식 투자 시뮬레이터' 서비스의 한국 주식 투자 상담 AI다.\n"
        "- 수익률을 보장하지 말고, 항상 리스크와 장단점을 설명해라.\n"
        "- 사용자가 종목을 지정한 경우, 아래 [뉴스 분석 요약] 정보를 적극적으로 활용해라.\n"
        "- 너무 장문으로 말하지 말고 5~10문장 정도로 핵심만 정리해라.\n"
    )

    if sentiment_text:
        system_prompt += f"\n[뉴스 분석 요약]\n{sentiment_text}\n[요약 끝]\n"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    try:
        return generate_response(messages)
    except Exception as e:
        return f"AI 모델 오류: {e}"
