# X-AI-Recommend

뉴스 기반 코스피/코스닥 주식 추천 웹 서비스 및 LLM 기반 금융 분석 플랫폼입니다.

## Project Structure

```
X-AI-Recommend
├── Web/                # Django Web Server (User Interface)
├── crawling/           # News Crawler & Sentiment Analysis (KR-FinBERT)
├── ai/                 # AI Model & Data Processing
├── calling_api/        # External API Manager (Korea Investment & Securities)
└── docker-compose.yml  # Docker Orchestration
```

## Components

### 1. Web (Django)
- 사용자 인터페이스를 제공하는 웹 서버입니다.
- 주식 검색, 시세 확인, AI 투자 추천 및 질의응답 기능을 제공합니다.

### 2. Crawling
- 네이버 금융에서 주식 관련 뉴스를 크롤링합니다.
- `KR-FinBERT` 모델을 사용하여 뉴스 기사의 감성(긍정/부정/중립)을 분석하고 점수화합니다.

### 3. AI
- 주식 데이터와 뉴스 분석 결과를 결합하여 투자 전략을 수립하거나 추천 알고리즘을 수행하는 모듈입니다.

### 4. Calling API
- 한국투자증권 API 등 외부 금융 API와 연동하여 실시간 주가 정보 및 계좌 정보를 가져옵니다.

## Deployment

이 프로젝트는 Docker 컨테이너 기반으로 배포되도록 설계되었습니다.

### Prerequisites
- Docker
- Docker Compose

### How to Run
```bash
# 프로젝트 루트 디렉토리에서 실행
docker-compose up --build
```
- `docker-compose.yml` 파일을 통해 각 서비스(Web, Crawler 등)가 컨테이너로 실행됩니다.
