import json
import os

# 파일 경로
prices_path = "./db/all_prices_noname.json"
codes_path = "./db/market_code.json"
output_path = "./db/all_prices.json"

# JSON 로드
with open(prices_path, "r", encoding="utf-8") as f:
    prices = json.load(f)

with open(codes_path, "r", encoding="utf-8") as f:
    code_map_raw = json.load(f)

# code → company 로 역매핑
code_to_company = {v["code"]: k for k, v in code_map_raw.items()}

# 새로운 리스트 생성
output = []
for item in prices:
    iscd = item.get("iscd")
    company = code_to_company.get(iscd)
    
    # 회사명이 존재하면 company 필드 추가
    new_item = item.copy()
    if company:
        new_item["company"] = company
    
    output.append(new_item)

# 결과 저장
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
