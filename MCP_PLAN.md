# MCP Integration Plan

## 목적
뉴스 크롤링·감성 분석 파이프라인을 반복적으로 실행하면서도, 대용량 데이터/모델과의 상호작용을 안전하게 자동화하고자 MCP 기반 도구를 도입한다. 아래 계획은 팀이 우선 연결해야 할 MCP 서버와 단계별 작업 순서를 정리한 것이다.

## 추천 MCP 서버
- **filesystem**: `filemanager` 또는 `fs` 계열 서버를 연결해 `crawling/db`와 `log/`의 대용량 JSON·로그를 안전하게 읽고 부분 수정한다. 파일 잠금이나 버전 스냅샷 기능이 있으면 크롤링/분석 결과 검증에 유리하다.
- **shell**: `shell` MCP를 붙이면 동일한 환경에서 `python crawling/main.py`, `docker build` 등 반복 명령을 에이전트가 직접 실행하고 로그를 회수할 수 있다.
- **http / fetch**: 기사/모델 API 호출을 프록시하기 위해 `http` MCP가 필요하다. 네이버 뉴스나 Hugging Face Endpoint 호출을 표준화된 인터페이스로 감싸 두면 환경별 토큰 주입이 쉬워진다.
- **secrets**: `vault` 혹은 `env` MCP로 API 키(KR-FinBERT 토큰, Hugging Face token, DB 접속 정보 등)를 안전하게 저장하고 세션마다 주입한다.
- **git** (선택): `git` MCP를 연결하면 자동 리베이스, 커밋 메시지 템플릿 적용, 히스토리 정리(`git filter-repo`) 같은 반복 작업을 에이전트가 직접 처리할 수 있다.





## 연결 및 운영 계획
### Phase 1 · 준비
- [x] **우선순위 정의**: 크롤러 자동화를 최우선으로 두고 shell → filesystem → secrets 순으로 연결 순서를 확정한다.
- [x] **환경 점검**: `python3`, Docker, git 버전과 네트워크 권한을 확인해 MCP 서버들이 동일한 러너에서 동작하도록 보장한다.

### Phase 2 · 구성
- [ ] **접속 정보 준비**: 각 MCP 서버의 endpoint·token을 `.mcp/config.json`에 기록하고, 민감 값은 secrets MCP에만 저장한다.
- [ ] **권한 검증**: shell MCP로 `python crawling/main.py --help`를 실행해 명령 위임이 가능한지 확인한다.

### Phase 3 · 검증
- [ ] **테스트 시나리오 작성**: `python crawling/news_crawler.py --limit 5` 같은 소규모 시나리오를 shell MCP 명령으로 등록해 헬스체크에 사용한다.
- [ ] **파일 워크플로 검토**: filesystem MCP로 `crawling/db/response.json`의 부분 읽기/쓰기 테스트를 수행해 대용량 처리 안정성을 확인한다.

### Phase 4 · 운영
- [ ] **자동화 배치**: MCP 조합을 이용해 “기사 크롤링→감성 분석→요약” 파이프라인을 일 배치로 구성하고, 실패 시 로그를 자동 수집한다.
- [ ] **확장 고려**: 웹/프런트 작업이 본격화되면 http 및 browser MCP를 추가 연결해 프록시 호출·스크린샷 수집을 자동화한다.

이 계획을 바탕으로 MCP 서버를 순차 도입하면, 크롤링·분석·배포 작업 전반이 자동화되어 협업 속도를 올릴 수 있다.
