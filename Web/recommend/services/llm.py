# recommend/services/llm.py
import os
import torch
import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from .sentiment import format_sentiment_summary

# Project Root (Web/recommend/services/llm.py -> ... -> Root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "ai" / "models"
MODEL_ID = "Bllossom/llama-3.2-Korean-Bllossom-3B"

# Data Paths
FOR_LLM_PATH = BASE_DIR / "ai" / "db" / "for_llm.json"
ALL_PRICES_PATH = BASE_DIR / "calling_api" / "db" / "all_prices.json"

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
        
        # Check CUDA availability
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"DEBUG: Torch device available: {device}")

        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_DIR,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
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
    import time
    start_time = time.time()
    
    load_model()
    
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token

    print("DEBUG: Applying chat template...")
    input_ids = _tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(_model.device)

    terminators = [
        _tokenizer.eos_token_id,
        _tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    print(f"DEBUG: Starting generation (max_tokens={max_new_tokens})...")
    with torch.no_grad():
        outputs = _model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            eos_token_id=terminators,
            do_sample=True,
            temperature=temperature,
            top_p=0.9,
            pad_token_id=_tokenizer.pad_token_id
        )
    
    gen_time = time.time() - start_time
    print(f"DEBUG: Generation finished in {gen_time:.2f}s")

    response = outputs[0][input_ids.shape[-1]:]
    return _tokenizer.decode(response, skip_special_tokens=True)


def load_recommendations(top_n: int = 50) -> str:
    """for_llm.json에서 상위 N개 종목 정보를 문자열로 요약 반환"""
    if not FOR_LLM_PATH.exists():
        return ""
    
    try:
        with open(FOR_LLM_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 상위 N개만 사용
        top_data = data[:top_n]
        
        summary_lines = []
        for idx, item in enumerate(top_data, 1):
            line = (
                f"{idx}. {item['name']} "
                f"(점수:{item['score']}, 긍정:{item['positive']}, 부정:{item['negative']}, "
                f"중립:{item['neutral']}, 기사수:{item['total_articles']}, 현재가:{item.get('price', 'N/A')})"
            )
            summary_lines.append(line)
            
        return "\n".join(summary_lines)
    except Exception as e:
        print(f"Error loading recommendations: {e}")
        return ""

def find_stock_price(question: str) -> str:
    """질문에 포함된 종목명을 all_prices.json에서 찾아 가격 정보를 반환"""
    if not ALL_PRICES_PATH.exists():
        return ""
        
    try:
        with open(ALL_PRICES_PATH, "r", encoding="utf-8") as f:
            prices = json.load(f)
            
        found_info = []
        for p in prices:
            company = p.get("company")
            if company and company in question:
                info = (
                    f"- {company}: 현재가 {p.get('stck_prpr')}원 "
                    f"(기준시간: {p.get('timestamp')})"
                )
                found_info.append(info)
                
        if found_info:
            return "\n".join(found_info) + "\n(정확한 최신 정보는 우측 가격 검색 기능을 이용하세요.)"
        return ""
    except Exception as e:
        print(f"Error loading prices: {e}")
        return ""

def ask_invest_ai(question: str, stock_name: str | None = None) -> str:
    """
    question: 사용자가 입력한 질문
    stock_name: 현재 선택된 종목명 (예: '삼성전자')
    """

    sentiment_text = None
    if stock_name:
        sentiment_text = format_sentiment_summary(stock_name)

    # 1. 추천 종목 리스트 로드 (상위 20개 정도로 제한하여 토큰 절약)
    recommendations = load_recommendations(top_n=20)
    
    # 2. 질문에 포함된 종목의 가격 정보 검색
    price_info = find_stock_price(question)

    system_prompt = (
        "너는 'AI 주식 투자 시뮬레이터' 서비스의 한국 주식 투자 상담 AI다.\n"
        "- 수익률을 보장하지 말고, 항상 리스크와 장단점을 설명해라.\n"
        "- 기본적인 주식 용어(재무제표, PER 등)에 대해 물어보면 친절하게 설명해라.\n"
        "- 너무 장문으로 말하지 말고 5~10문장 정도로 핵심만 정리해라.\n"
    )
    
    if recommendations:
        system_prompt += (
            f"\n[현재 AI 추천 상위 종목 (근거: 뉴스 감성 분석 점수)]\n"
            f"{recommendations}\n"
            f"사용자가 추천을 원하면 위 리스트를 참고하여 점수와 뉴스 긍/부정 비율을 근거로 설명해라.\n"
        )
        
    if price_info:
        system_prompt += (
            f"\n[가격 정보 조회 결과]\n"
            f"{price_info}\n"
            f"사용자가 가격을 물어보면 위 정보를 그대로 전달하고, 정확한 정보는 우측 검색을 이용하라고 안내해라.\n"
        )

    if sentiment_text:
        system_prompt += f"\n[선택된 종목 뉴스 분석 요약]\n{sentiment_text}\n[요약 끝]\n"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    try:
        return generate_response(messages)
    except Exception as e:
        return f"AI 모델 오류: {e}"
