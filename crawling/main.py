# crawling/main.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import time
from crawling.news_crawler import crawl_all_news
from analyze import analyze_and_score


# === 경로 설정 ===
BASE_DIR = Path(__file__).resolve().parent       # .../crawling
ROOT_DIR = BASE_DIR.parent                       # 프로젝트 루트
DB_DIR = BASE_DIR / "db"
LOG_DIR = BASE_DIR / "log"

DB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

MARKET_CODE_PATH = DB_DIR / "market_code.json"
RESPONSE_JSON_PATH = DB_DIR / "response.json"
LOG_FILE_PATH = LOG_DIR / "main.log"


# === 로깅 설정 ===
def setup_logging() -> logging.Logger:
    """
    메인 파이프라인용 로거 설정.
    각 모듈(news_crawler, analyze)도 logger = logging.getLogger(__name__)
    이런 식으로 가져다 쓰면 동일 핸들러를 공유하게 됨.
    """
    logger = logging.getLogger("crawling_main")
    logger.setLevel(logging.INFO)

    # 중복 핸들러 방지
    if logger.handlers:
        return logger

    # 파일 로거 (롤링)
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    file_handler.setFormatter(formatter)

    # 콘솔 로거
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False  # root 로거로 중복 출력 방지

    return logger


class NewsPipelineService:
    """
     Invest 뉴스 크롤링 + 감성 점수 계산 파이프라인 서비스.
    - news_crawler.crawl_all_news 실행
    - analyze.analyze_and_score 실행
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

        # 환경변수에서 크롤링 속도 등 설정 (docker-compose에서 넘겨줄 수 있음)
        self.sleep_seconds = float(os.getenv("CRAWLER_SLEEP_SECONDS", "0.2"))
        self.logger.info(f"CRAWLER_SLEEP_SECONDS = {self.sleep_seconds}")

        # 필요하면 DB 관련 ENV도 여기서 읽으면 됨 (지금은 사용 X)
        # self.db_host = os.getenv("DB_HOST")
        # self.db_user = os.getenv("DB_USER")
        # self.db_password = os.getenv("DB_PASSWORD")

        self.logger.info("NewsPipelineService initialized")

    def run_once(self):
        """
        한 번의 파이프라인 실행:
        1) 종목 코드 기반 뉴스 20000개 크롤링
        2) 각 뉴스에 감성 점수(-5~+5) 부여
        3) /crawling/db/response.json 에 저장
        """
        self.logger.info("===== Start  News pipeline (one-shot) =====")

        # 1) 입력 파일 체크
        if not MARKET_CODE_PATH.exists():
            self.logger.error(f"market_code.json not found at {MARKET_CODE_PATH}")
            return

        # 2) 뉴스 크롤링
        self.logger.info("Step 1: Crawling news from Invest")
        start_time = time.time()
        articles = crawl_all_news(
            market_code_path=MARKET_CODE_PATH,
            sleep_seconds=self.sleep_seconds,
            logger=self.logger,
        )
        elapsed_crawl = time.time() - start_time
        self.logger.info(
            f"Step 1 done. Crawled {len(articles)} articles "
            f"in {elapsed_crawl:.2f} seconds."
        )

        # 3) 감성 분석 + JSON 저장
        self.logger.info("Step 2: Sentiment analysis & save to JSON")
        start_time = time.time()
        analyze_and_score(
            articles=articles,
            output_path=RESPONSE_JSON_PATH,
            logger=self.logger,
        )
        elapsed_analyze = time.time() - start_time
        self.logger.info(
            f"Step 2 done in {elapsed_analyze:.2f} seconds. "
            f"Output: {RESPONSE_JSON_PATH}"
        )

        total_elapsed = time.time() - start_time
        self.logger.info(
            f"===== End  News pipeline. Total elapsed: {total_elapsed:.2f} seconds ====="
        )


def main():
    logger = setup_logging()
    logger.info("Starting  News Crawler + Analyzer pipeline")

    try:
        service = NewsPipelineService(logger)
        service.run_once()
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.exception(f"Fatal error in pipeline: {e}")
        raise


if __name__ == "__main__":
    main()
