# api 호출 디렉터리

1. full_call.py로 all_prices_noname.json 생성
2. make_all_prices.py로 all_prices.json 만듬(기업명 추가)
3. ../ai/stock_data.py로 LLM이 읽을 기업 점수 + 기업 현재가 적혀있는 for_llm.json 생성

token_manager.py 파일과 app.py 파일로 토큰 20시간마다 재발급