# news_crawler.py
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---- 경로 상수 ----
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DEBUG_DIR = BASE_DIR / "debug"

DEBUG_DIR.mkdir(parents=True, exist_ok=True)

# ---- 시장 관련 상수 ----
KOSPI_MARKET_KEY = "J"
KOSDAQ_MARKET_KEY = "U"

N_KOSPI = 3   # 검색할 코스피 종목 개수
N_KOSDAQ = 0  # 검색할 코스닥 종목 개수
N_NEWS_PER_STOCK = 3  # 검색할 종목당 뉴스 개수

REQUEST_TIMEOUT = 10

# ✅ 네이버 증권 "뉴스·공시" 탭에서 실제 뉴스 리스트를 뿌리는 iframe 주소
BASE_LIST_URL = (
    "https://finance.naver.com/item/news_news.naver"
    "?code={code}&page={page}&clusterId="
)
BASE_READ_URL = "https://finance.naver.com"  # 상대 경로용 베이스 URL


# ---------------------------------------------------
# 공통 유틸
# ---------------------------------------------------
def load_market_codes(path: Path) -> Dict[str, Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def _parse_date(date_text: str) -> datetime:
    """날짜 텍스트를 datetime 객체로 변환 (예전 async 코드 재사용)"""
    try:
        # "2024.07.13 15:30" 형식 파싱
        date_pattern = r"(\d{4})\.(\d{2})\.(\d{2})\s+(\d{2}):(\d{2})"
        match = re.search(date_pattern, date_text)

        if match:
            year, month, day, hour, minute = map(int, match.groups())
            return datetime(year, month, day, hour, minute)

        # 상대 시간 파싱 ("1시간 전", "2일 전" 등)
        if "분 전" in date_text:
            minutes = int(re.search(r"(\d+)분", date_text).group(1))
            return datetime.now() - timedelta(minutes=minutes)
        elif "시간 전" in date_text:
            hours = int(re.search(r"(\d+)시간", date_text).group(1))
            return datetime.now() - timedelta(hours=hours)
        elif "일 전" in date_text:
            days = int(re.search(r"(\d+)일", date_text).group(1))
            return datetime.now() - timedelta(days=days)

    except Exception as e:
        logger.warning(f"Failed to parse date '{date_text}': {str(e)}")

    return datetime.now()


def select_top_codes(
    market_data: Dict[str, Dict[str, Any]],
    market_key: str,
    limit: int,
) -> List[Dict[str, Any]]:
    """
    market_code.json 기준으로 특정 시장(KOSPI/KOSDAQ)의 상위 몇 개 종목만 추리기
    (지금은 단순히 종목코드 순 정렬 후 앞에서 limit개 자름)
    """
    items: List[Dict[str, Any]] = []
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


# ---------------------------------------------------
# 리스트 페이지 파싱
# ---------------------------------------------------
def parse_news_list_from_list_page(html: str, max_items: int) -> List[Dict[str, Any]]:
    """
    /item/news_news.naver 의 HTML에서
    뉴스 제목 + 상세 URL(네이버 뉴스 읽기 페이지) + 날짜를 뽑는다.
    """
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, Any]] = []

    # 기본 구조: table.type2 안의 tr 들
    rows = soup.select("table.type2 tr")

    for tr in rows:
        if len(results) >= max_items:
            break

        title_link = tr.select_one("td.title a")
        if not title_link:
            continue

        title = title_link.get_text(strip=True)
        href = title_link.get("href", "").strip()
        if not title or not href:
            continue

        # 상대/절대 URL 모두 처리
        if href.startswith("http"):
            url = href
        elif href.startswith("/"):
            url = BASE_READ_URL + href
        else:
            url = BASE_READ_URL + "/" + href.lstrip("/")

        # 날짜(td.date) 추출 시도
        date_td = tr.select_one("td.date")
        if date_td:
            date_text = date_td.get_text(strip=True)
            published_at = _parse_date(date_text).isoformat()
        else:
            published_at = datetime.now().isoformat()

        results.append(
            {
                "title": title,
                "detail_url": url,
                "published_at": published_at,
            }
        )

    # 그래도 아무것도 안 나왔으면, 예전 방식으로 한 번 더 시도
    if not results:
        links = soup.select("table.type2 td.title a")
        if not links:
            links = soup.select("td.title a")
        if not links:
            all_links = soup.find_all("a", href=True)
            links = [
                a for a in all_links
                if "item/news_read.naver" in a["href"]
            ]

        for a in links[:max_items]:
            title = a.get_text(strip=True)
            href = a.get("href", "").strip()
            if not title or not href:
                continue

            if href.startswith("http"):
                url = href
            elif href.startswith("/"):
                url = BASE_READ_URL + href
            else:
                url = BASE_READ_URL + "/" + href.lstrip("/")

            results.append(
                {
                    "title": title,
                    "detail_url": url,
                    "published_at": datetime.now().isoformat(),
                }
            )

    if not results:
        logger.warning("parse_news_list: no news items found on page")
        return results

    logger.info(f"parse_news_list: extracted {len(results)} items from list page")
    return results


# ---------------------------------------------------
# 상세 기사 파싱 (네이버 뉴스 일반 페이지용)
# ---------------------------------------------------
def _parse_naver_news_html(html: str) -> Dict[str, str]:
    """네이버 뉴스(통합/모바일 등) HTML에서 제목/본문 텍스트 추출."""
    soup = BeautifulSoup(html, "html.parser")

    # 제목 후보들
    title_el = (
        soup.select_one("h2#title_area")
        or soup.select_one("h2.media_end_head_headline")
        or soup.select_one("h3#articleTitle")          # 예전 스타일
        or soup.select_one("h1#news_headline")         # 기타 예외
    )
    title = title_el.get_text(strip=True) if title_el else ""

    # 본문 후보들
    content_el = (
        soup.select_one("article#dic_area")           # 통합 뉴스
        or soup.select_one("div#newsct_article")      # 통합 뉴스 다른 케이스
        or soup.select_one("div#articleBodyContents") # 예전 스타일
        or soup.select_one("div.article_view")        # 일부 언론사 자체 템플릿
    )

    content = ""
    if content_el:
        for tag in content_el(["script", "style"]):
            tag.decompose()
        content = content_el.get_text(" ", strip=True)

    return {"title": title, "content": content}


def fetch_article_detail(session, url: str) -> dict | None:
    """
    네이버 금융 기사 상세 페이지 크롤링
    - 금융 wrapper(.articleSubject, .articleCont) 우선 시도
    - 실패/너무 짧으면 통합 뉴스/모바일 구조(_parse_naver_news_html)로 재시도
    """
    logger.info(f"Requesting article page: {url}")
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch article page {url}: {e}")
        return None

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # ----------------------------
    # 1차: 네이버 금융 wrapper 스타일 (.articleSubject, .articleCont)
    # ----------------------------
    title_elem = soup.select_one(".articleSubject")
    content_elem = soup.select_one(".articleCont")

    title = title_elem.get_text(strip=True) if title_elem else ""
    content = ""
    if content_elem:
        for tag in content_elem(["script", "style"]):
            tag.decompose()
        content = content_elem.get_text(" ", strip=True)

    # ----------------------------
    # 2차: 통합 뉴스/모바일 등의 공통 파서로 재시도
    #  - news.naver.com 의 #dic_area, #newsct_article 등
    # ----------------------------
    if len(title) < 5 or len(content) < 50:
        parsed = _parse_naver_news_html(html)
        if parsed.get("title"):
            title = parsed["title"]
        if parsed.get("content"):
            content = parsed["content"]

    # ----------------------------
    # 날짜 파싱
    # ----------------------------
    published_at = datetime.now()

    # 금융 wrapper 쪽 날짜
    date_elem = soup.select_one(".article_info .dates")
    date_text = ""
    if date_elem:
        date_text = date_elem.get_text(strip=True)

    # 통합 뉴스 쪽 날짜 (news.naver.com)
    if not date_text:
        time_el = soup.select_one(".media_end_head_info_datestamp_time")
        if time_el:
            date_text = time_el.get_text(strip=True)

    if date_text:
        published_at = _parse_date(date_text)

    # ----------------------------
    # 최종 유효성 체크
    # ----------------------------
    if not title or len(content) < 50:
        logger.warning(
            f"Article seems invalid (title/content too short): {url} "
            f"(title_len={len(title)}, content_len={len(content)})"
        )
        # 디버그용으로 HTML 저장해서 나중에 구조 살펴보고 싶으면 주석 해제
        # try:
        #     fname = DEBUG_DIR / ("article_" + re.sub(r'[^0-9A-Za-z]+', '_', url) + ".html")
        #     fname.write_text(html, encoding="utf-8")
        #     logger.info(f"Saved debug article HTML to: {fname}")
        # except Exception as e:
        #     logger.error(f"Failed to save article HTML debug: {e}")
        return None

    return {
        "title": title,
        "content": content,
        "url": url,
        "published_at": published_at.isoformat(),
        "source": "naver_finance",
    }


# ---------------------------------------------------
# 종목별 뉴스 크롤링
# ---------------------------------------------------
def fetch_company_news(
    session: requests.Session,
    company: Dict[str, Any],
    max_items: int,
) -> List[Dict[str, Any]]:
    name = company["name"]
    code = company["code"]
    market = company["market"]

    logger.info(f"[{market}] {name}({code}) -> Naver Finance news")

    collected: List[Dict[str, Any]] = []
    page = 1

    # 페이지를 3페이지까지만 탐색 (너무 많이 타지 않도록 제한)
    while len(collected) < max_items and page <= 3:
        url = build_list_url(code, page=page)
        logger.info(f"Requesting list page {page}: {url}")

        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed for {name}({code}) page {page}: {e}")
            break

        # 🔍 디버그용 HTML 저장
        debug_path = DEBUG_DIR / f"{code}_page{page}.html"
        try:
            debug_path.write_text(resp.text, encoding="utf-8")
            logger.info(f"Saved debug HTML to: {debug_path}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML for {code} page {page}: {e}")

        # 리스트 페이지에서 제목+URL(+날짜) 추출
        rough_list = parse_news_list_from_list_page(
            resp.text,
            max_items=max_items - len(collected),
        )

        if not rough_list:
            logger.info(f"No more articles found for {name}({code}) at page {page}")
            break

        # 각 리스트 아이템에 대해 실제 기사 상세 페이지에서 내용 추출
        for item in rough_list:
            if len(collected) >= max_items:
                break

            detail_url = item["detail_url"]

            # 1차: 상세 페이지 시도
            article = fetch_article_detail(session, detail_url)

            # 2차: 실패하면 리스트 정보만으로라도 기사 객체 생성
            if not article:
                article = {
                    "title": item["title"],
                    "content": "",
                    "url": detail_url,
                    "published_at": item.get(
                        "published_at", datetime.now().isoformat()
                    ),
                    "source": "naver_finance_list",
                }

            # 공통으로 회사 정보 붙여주기
            article["company_name"] = name
            article["company_code"] = code
            article["market"] = market

            collected.append(article)
            # 너무 빠르게 도배하지 않도록 살짝 딜레이
            time.sleep(0.1)

        page += 1

    logger.info(f"Collected {len(collected)} articles for {name}({code})")
    return collected


# ---------------------------------------------------
# 전체 시장 돌리기 + 파일로 저장
# ---------------------------------------------------
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
            "Referer": "https://finance.naver.com/",
        }
    )

    crawling_data: Dict[str, List[Dict[str, Any]]] = {}

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


# ---------------------------------------------------
# 실행 엔트리
# ---------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )

    crawl_all_to_file(
        market_code_path=DB_DIR / "market_code.json",
        output_path=DB_DIR / "crawling.json",
        sleep_seconds=0.2,
    )
