# crawling/toss_news_crawler.py
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

KOSPI_MARKET_KEY = "J"
KOSDAQ_MARKET_KEY = "U"

N_KOSPI = 3 # 검색할 코스피 종목 개수
N_KOSDAQ = 0 # 검색할 코스닥 종목 개수
N_NEWS_PER_STOCK = 10

REQUEST_TIMEOUT = 10
BASE_LIST_URL = "https://finance.naver.com/item/news_news.naver?code={code}&page={page}"
BASE_READ_URL = "https://finance.naver.com"  # 상세 페이지는 상대 경로를 붙여서 사용


def load_market_codes(path: Path) -> Dict[str, Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def select_top_codes(
    market_data: Dict[str, Dict[str, Any]],
    market_key: str,
    limit: int,
) -> List[Dict[str, Any]]:
    items = []
    for name, info in market_data.items():
        if info.get("market") == market_key:
            code = info.get("code")
            if not code:
                continue
            items.append(
                {
                    "name": name,
                    "code": code,
                    "market": market_key,
                }
            )

    items.sort(key=lambda x: x["code"])
    return items[:limit]


def build_list_url(code: str, page: int = 1) -> str:
    return BASE_LIST_URL.format(code=code, page=page)


def parse_news_list_from_list_page(html: str, max_items: int) -> List[Dict[str, str]]:
    """
    네이버 금융 종목 뉴스 목록 페이지에서
    제목/상세 링크를 추출하고, content는 일단 빈 문자열로 둔다.
    """
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, str]] = []

    # 네이버 금융 뉴스 테이블: 보통 class="type2"
    table = soup.select_one("table.type2")
    if not table:
        logger.warning("parse_news_list: table.type2 not found")
        return results

    rows = table.select("tr")
    for row in rows:
        title_td = row.select_one("td.title")
        if not title_td:
            continue

        link = title_td.select_one("a")
        if not link:
            continue

        title = link.get_text(strip=True)
        if not title:
            continue

        href = link.get("href", "")
        news_url = BASE_READ_URL + href if href.startswith("/") else href

        # 지금은 본문까지 안 들어가고, 제목 위주로만 사용
        content = ""

        results.append(
            {
                "title": title,
                "content": content,
                "detail_url": news_url,
            }
        )

        if len(results) >= max_items:
            break

    logger.info(
        f"parse_news_list: extracted {len(results)} items from list page "
        f"(max_items={max_items})"
    )

    return results



def fetch_company_news(
    session: requests.Session,
    company: Dict[str, Any],
    max_items: int,
) -> List[Dict[str, str]]:
    name = company["name"]
    code = company["code"]
    market = company["market"]

    logger.info(f"[{market}] {name}({code}) -> Naver Finance news")

    collected: List[Dict[str, str]] = []
    page = 1

    while len(collected) < max_items and page <= 3:  # 필요하면 page 제한 조절
        url = build_list_url(code, page=page)
        logger.info(f"Requesting list page {page}: {url}")

        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed for {name}({code}) page {page}: {e}")
            break

        articles = parse_news_list_from_list_page(
            resp.text,
            max_items=max_items - len(collected),
        )
        if not articles:
            logger.info(f"No more articles found for {name}({code}) at page {page}")
            break

        collected.extend(articles)
        page += 1
        time.sleep(0.2)

    logger.info(f"Collected {len(collected)} articles for {name}({code})")
    # detail_url은 나중에 쓸 수 있으니 일단 유지하거나, 필요 없으면 제거
    for item in collected:
        item.pop("detail_url", None)

    return collected


def crawl_all_to_file(
    market_code_path: Path,
    output_path: Path,
    sleep_seconds: float = 0.2,
):
    logger.info(f"Loading market codes from: {market_code_path}")
    market_data = load_market_codes(market_code_path)

    kospi_list = select_top_codes(market_data, KOSPI_MARKET_KEY, N_KOSPI)
    kosdaq_list = select_top_codes(market_data, KOSDAQ_MARKET_KEY, N_KOSDAQ)
    targets = kospi_list + kosdaq_list

    logger.info(
        f"Selected {len(kospi_list)} KOSPI + {len(kosdaq_list)} KOSDAQ = "
        f"{len(targets)} total companies"
    )

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/129.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    )

    crawling_data: Dict[str, List[Dict[str, str]]] = {}

    total = len(targets)
    for idx, company in enumerate(targets, start=1):
        name = company["name"]
        logger.info(f"=== [{idx}/{total}] {name} ({company['code']}) ===")
        articles = fetch_company_news(session, company, N_NEWS_PER_STOCK)
        if articles:
            crawling_data[name] = articles

        time.sleep(sleep_seconds)

    logger.info(
        f"Crawling finished. Companies with news: {len(crawling_data)}"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(crawling_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved crawling data to: {output_path}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    BASE_DIR = Path(__file__).resolve().parent
    DB_DIR = BASE_DIR / "db"
    crawl_all_to_file(
        market_code_path=DB_DIR / "market_code.json",
        output_path=DB_DIR / "crawling.json",
        sleep_seconds=0.2,
    )