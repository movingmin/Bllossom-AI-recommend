import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from pathlib import Path


def get_market_top_n(sosok: int, pages: int = 20) -> pd.DataFrame:
    """
    네이버 금융 시가총액 상위 종목 크롤링
    sosok=0: KOSPI, sosok=1: KOSDAQ
    pages: 한 시장에서 긁을 페이지 수 (1페이지 = 50종목 → 20페이지 = 1000종목)
    """
    base_url = f"https://finance.naver.com/sise/sise_market_sum.nhn?sosok={sosok}&page="
    headers = {"User-Agent": "Mozilla/5.0"}
    result = []

    for page in range(1, pages + 1):
        url = f"{base_url}{page}"
        res = requests.get(url, headers=headers)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        table = soup.select_one("table.type_2")
        if table is None:
            continue

        rows = table.select("tbody tr")

        for row in rows:
            cols = row.select("td")
            if len(cols) < 2:
                continue

            link = cols[1].select_one("a")
            if not link:
                continue

            name = link.text.strip()
            href = link.get("href", "")
            if "code=" not in href:
                continue
            code = href.split("code=")[-1]

            # 시가총액 (숫자로 변환 시도)
            market_cap_text = cols[6].text.strip().replace(",", "")
            market_cap = int(market_cap_text) if market_cap_text.isdigit() else None

            result.append(
                {
                    "종목명": name,
                    "종목코드": code,
                    "시가총액": market_cap,
                }
            )

    return pd.DataFrame(result)


def convert_to_json_map(df_kospi: pd.DataFrame, df_kosdaq: pd.DataFrame) -> dict:
    """
    두 시장 DataFrame을 하나의 JSON 맵으로 변환

    {
      "종목명": {"code": "종목코드", "market": "J" 또는 "U"},
      ...
    }
    """
    result = {}

    # KOSPI (market = "J")
    for _, row in df_kospi.iterrows():
        name = row["종목명"]
        code = row["종목코드"]
        result[name] = {"code": code, "market": "J"}

    # KOSDAQ (market = "U")
    for _, row in df_kosdaq.iterrows():
        name = row["종목명"]
        code = row["종목코드"]
        # 이름이 겹치면 KOSDAQ으로 덮어쓸지 말지는 상황에 따라 다르지만,
        # 여기선 단순히 덮어쓰지 않고 없을 때만 추가
        if name not in result:
            result[name] = {"code": code, "market": "U"}

    return result


if __name__ == "__main__":
    # 각 시장별 시총 상위 1000 (20페이지 * 50)
    df_kospi = get_market_top_n(sosok=0, pages=20)   # KOSPI
    df_kosdaq = get_market_top_n(sosok=1, pages=20)  # KOSDAQ

    json_map = convert_to_json_map(df_kospi, df_kosdaq)

    # ./db/market_code.json 으로 저장
    db_dir = Path("./db")
    db_dir.mkdir(parents=True, exist_ok=True)
    output_path = db_dir / "market_code.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(json_map, f, ensure_ascii=False, indent=2)

    print(f"market_code.json 생성 완료 → {output_path.resolve()}")
