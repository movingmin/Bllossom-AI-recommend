# 뉴스 기사 crawling 디렉터리

## tree
```
/crawling
├── Dockerfile              # Docker 설정 파일
├── requirements.txt        # Dockerfile이 참조하여 설치할 의존성 패키지
├── crolling_market.py      # 네이버 금융 시가총액 상위 기업 크롤링 (market_code.json 생성)
├── news_crawler.py         # 기업 별 최신 기사 50개 크롤링 후 crawling.json 파일 작성
├── analyze.py              # crawling.json 파일을 토대로 Huggingface에서 transformers라이브러리로 KR-FinBERT
│                            (금융 감성 분석 LLM) 호출 후 기사에 대한 감성 점수 할당 - company_scores.json에 점수 게시
└── db
    ├── market_code.json    # 코스피 1000개, 코스닥 1000개 시가총액 상위 기업 저장 파일
    ├── crawling.json       # 크롤링 결과 (기업 → 기사 50개)
    └── company_scores.json # 감성 분석 결과 (기업별 점수 합산)
```

## 작동 원리
```
1. crolling_market.py 실행
   - 네이버 금융에서 코스피/코스닥 시가총액 상위 종목을 크롤링하여 db/market_code.json 생성

2. news_crawler.py 실행
   - market_code.json 확인, 상위 기업들의 기사 50개씩 크롤링
   - 기사 제목 / 내용을 db/crawling.json 파일에 작성

3. analyze.py 실행
   - crawling.json 파일의 기사 제목 / 내용을 Huggingface의 KR-FinBERT-SC(금융 분석(한국어)전문 LLM) 을 호출해서 감성 점수를 매기게 함
   - 감성 분석 결과를 db/company_scores.json에 정리 후 기업 별 점수 매김
```