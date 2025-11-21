from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any


# === 경로 상수 ===
SCORES_PATH = Path("../crawling/db/company_scores.json")
PRICES_PATH = Path("../calling_api/db/all_prices.json")
LLM_DATA_PATH = Path("../ai/db/for_llm.json")


# === 데이터 모델 ===

@dataclass
class CompanyData:
    name: str
    score: Optional[float] = None
    positive: Optional[int] = None
    negative: Optional[int] = None
    neutral: Optional[int] = None
    total_articles: Optional[int] = None
    price: Optional[float] = None

    def to_llm_dict(self) -> Dict[str, Any]:
        """
        LLM 컨텍스트로 쓰기 좋은 형태로 변환.
        None 값은 빼서 깔끔하게 만든다.
        """
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


# === 내부 유틸 ===

def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_price(raw_price_obj: Any) -> Optional[float]:
    """
    all_prices.json 이 dict 형태일 때만 사용하는 보조 함수.

    예시:
    {
        "삼성전자": { "price": 72000 },
        "현대차": { "current_price": 180000 },
        ...
    }
    또는
    {
        "삼성전자": 72000,
        "현대차": 180000,
        ...
    }
    """
    if raw_price_obj is None:
        return None

    # 숫자 하나만 들어있는 경우
    if isinstance(raw_price_obj, (int, float)):
        return float(raw_price_obj)

    if isinstance(raw_price_obj, dict):
        # 자주 쓰이는 키 후보
        for key in ["price", "current_price", "trade_price", "close"]:
            if key in raw_price_obj:
                value = raw_price_obj[key]
                if isinstance(value, (int, float)):
                    return float(value)

    # 알 수 없는 형태면 None
    return None


def _parse_price_str(s: str) -> Optional[float]:
    """
    문자열 가격을 float로 변환.
    예: "100600" 또는 "1,006.50"
    """
    if s is None:
        return None
    if not isinstance(s, str):
        return None

    s = s.replace(",", "").strip()
    if not s:
        return None

    try:
        return float(s)
    except ValueError:
        return None


# === 외부에서 쓰는 핵심 함수들 ===

def load_company_data(
    scores_path: Path = SCORES_PATH,
    prices_path: Path = PRICES_PATH,
) -> Dict[str, CompanyData]:
    """
    company_scores.json + all_prices.json 두 개를 로드해서
    { 회사이름: CompanyData } 형태로 합쳐서 반환.

    - scores_path: ../crawling/db/company_scores.json
      예시:
      {
        "삼성전자": {
          "positive_count": ...,
          "negative_count": ...,
          "neutral_count": ...,
          "total_articles": ...,
          "company_score": ...
        },
        ...
      }

    - prices_path: ../calling_api/db/all_prices.json
      예시(현재 구조):
      [
        {
          "timestamp": "...",
          "iscd": "005930",
          "stck_prpr": "100600",
          "company": "삼성전자"
        },
        ...
      ]
    """
    raw_scores = _load_json(scores_path)
    raw_prices = _load_json(prices_path)

    companies: Dict[str, CompanyData] = {}

    # 1) 점수 기반으로 기본 뼈대 생성 (회사명 기준)
    for name, data in raw_scores.items():
        companies[name] = CompanyData(
            name=name,
            score=data.get("company_score"),
            positive=data.get("positive_count"),
            negative=data.get("negative_count"),
            neutral=data.get("neutral_count"),
            total_articles=data.get("total_articles"),
            price=None,  # 나중에 채워 넣음
        )

    # 2) 가격 정보 합치기

    # 2-1. dict[str, Any] 패턴도 여전히 지원
    if isinstance(raw_prices, dict):
        for name, price_obj in raw_prices.items():
            price = _extract_price(price_obj)
            if price is None:
                continue
            if name in companies:
                companies[name].price = price
            else:
                # 점수에는 없는데 가격만 있는 종목도 넣고 싶다면 유지
                companies[name] = CompanyData(
                    name=name,
                    price=price,
                )

    # 2-2. 지금 네 all_prices.json 패턴: list[dict]
    elif isinstance(raw_prices, list):
        for row in raw_prices:
            if not isinstance(row, dict):
                continue

            name = row.get("company") or row.get("hts_kor_isnm")
            if not name:
                continue

            raw_price = row.get("stck_prpr") or row.get("price")
            price = None
            if isinstance(raw_price, (int, float)):
                price = float(raw_price)
            elif isinstance(raw_price, str):
                price = _parse_price_str(raw_price)

            if price is None:
                continue

            if name in companies:
                companies[name].price = price
            else:
                # 점수는 없고 가격만 있는 종목도 필요하면 살려두기
                companies[name] = CompanyData(
                    name=name,
                    price=price,
                )

    return companies


def get_company(
    name: str,
    companies: Dict[str, CompanyData],
) -> Optional[CompanyData]:
    """
    특정 회사 이름으로 CompanyData 조회.
    없으면 None.
    """
    return companies.get(name)


def pick_top_companies(
    companies: Dict[str, CompanyData],
    top_n: int = 5,
    min_articles: int = 0,
) -> List[CompanyData]:
    """
    점수(score) 기준 상위 N개 종목을 뽑는다.
    - total_articles >= min_articles 조건을 만족하는 종목만 사용
    - score가 None인 종목은 제외
    """
    filtered: List[CompanyData] = []

    for c in companies.values():
        if c.score is None:
            continue
        if c.total_articles is not None and c.total_articles < min_articles:
            continue
        filtered.append(c)

    # score 내림차순 정렬
    filtered.sort(key=lambda x: x.score, reverse=True)

    return filtered[:top_n]


def to_llm_json(companies: List[CompanyData]) -> str:
    """
    LLM 프롬프트에 붙이기 좋은 JSON 문자열 생성.
    [
      { "name": "...", "score": ..., "total_articles": ..., "price": ... },
      ...
    ]
    형태로 직렬화한다.
    """
    data = [c.to_llm_dict() for c in companies]
    return json.dumps(data, ensure_ascii=False, indent=2)


def save_llm_json(
    companies: List[CompanyData],
    path: Path = LLM_DATA_PATH,
) -> None:
    json_str = to_llm_json(companies)
    path.parent.mkdir(parents=True, exist_ok=True)  # 디렉토리 없으면 생성
    with path.open("w", encoding="utf-8") as f:
        f.write(json_str)


if __name__ == "__main__":
    # 1. 두 JSON에서 데이터 로드
    company_map = load_company_data()

    # 2. 점수 상위 50개만 뽑는다 (기사 최소 20개 이상 예시)
    top_companies = pick_top_companies(company_map, top_n=50, min_articles=20)

    # 3. LLM용 JSON 파일로 저장
    save_llm_json(top_companies)
    print("저장 완료:", LLM_DATA_PATH)
