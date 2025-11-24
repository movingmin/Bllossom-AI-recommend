# recommend/services/llm.py
import os
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from .sentiment import format_sentiment_summary

# Project Root (Web/recommend/services/llm.py -> ... -> Root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "ai" / "models"
MODEL_ID = "Bllossom/llama-3.2-Korean-Bllossom-3B"

_model = None
_tokenizer = None

def load_model():
    global _model, _tokenizer
    if _model is not None:
        return

    print(f"Loading Local LLM: {MODEL_ID}...")
    try:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        
        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_DIR
        )
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_DIR,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        print("Local LLM loaded successfully.")
    except Exception as e:
        print(f"Failed to load Local LLM: {e}")
        raise e

def generate_response(messages: list, max_new_tokens: int = 512, temperature: float = 0.6) -> str:
    """
    messages: list of dict, e.g. [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    """
    load_model()
    
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token

    input_ids = _tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(_model.device)

    terminators = [
        _tokenizer.eos_token_id,
        _tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    with torch.no_grad():
        outputs = _model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            eos_token_id=terminators,
            do_sample=True,
            temperature=temperature,
            top_p=0.9,
        )

    response = outputs[0][input_ids.shape[-1]:]
    return _tokenizer.decode(response, skip_special_tokens=True)


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
