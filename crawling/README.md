# 뉴스 기사 crawling 디렉터리

## tree
```
/crawling
├── Dockerfile              # Docker 설정 파일
├── requirements.txt        # Dockerfile이 참조하여 설치할 의존성 패키지
├── main.py                 # main 실행 파일
├── news_crawler.py         # 네이버증권에서 2000개 기업 별 최신 기사 10개 크롤링 후 crawling.json 파일 작성
├── analyze.py              # crawling.json 파일을 토대로 Huggingface에서 transformers라이브러리로 KR-FinBERT
│                            (금융 감성 분석 LLM) 호출 후 기사에 대한 감성 점수 할당 - response.json에 점수 게시
│
├── db
│   ├── market_code.json    # 코스피 1000개, 코스닥 1000개 시가총액 상위 기업 저장 파일
│   ├── crawling.json       # 크롤링 결과 (기업 → 기사 10개)
│   └── response.json       # 감성 분석 결과 (기업별 점수 합산)
│
├── log
│   └── main.log            # 상태 확인을 위한 로그
```

## 작동 원리
```
1. main.py 실행
2. news_crawler.py를 통해 market_code.json 확인, 2000개 기업의 기사 10개씩 크롤링후 기사 제목 / 내용을 crawling.json 파일에 작성
3. analyze.py를 통해 crawling.json 파일의 기사 제목 / 내용을 Huggingface의 KR-FinBERT-SC(금융 분석(한국어)전문 LLM) 을 호출해서 감성 점수를 매기게 함, 감성 분석 결과를 response.json에 정리 후 기업 별 점수 매김
```