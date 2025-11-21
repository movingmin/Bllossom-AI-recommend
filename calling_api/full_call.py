import time
import requests
import logging
import json

URL_BASE = "https://openapivts.koreainvestment.com:29443"
PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"
API_URL = URL_BASE + PATH

APP_KEY = "PSfKEEmYWhmONmHuTOGxKfDcue4NsVCeMJZE"
APP_SECRET = "VSXnfPwJdEW81zQV5A6Giwf+Plq0czrO/9mMrdgdgwcN7Mds5ah/lILSNF9M/JnO4bleBmkcQEPTP109I6PZ4ru/DhZ55r/mTYg9jLfsBPvEJ/URyb4dGEYaNq2CoJeGEmViRzYOboVFhUCHfDI49L2aHs2Ky3U44TzP988h2I7HfyPK8MU="
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6ImU4ODUxMmZhLTYzNDUtNDY1OC04NWM5LTU3Nzc2OTMyMzE0NCIsInByZHRfY2QiOiIiLCJpc3MiOiJ1bm9ndyIsImV4cCI6MTc2MzcxNDI3MywiaWF0IjoxNzYzNjI3ODczLCJqdGkiOiJQU2ZLRUVtWVdobU9ObUh1VE9HeEtmRGN1ZTROc1ZDZU1KWkUifQ.qTLwTB2z3u7SyhrRi54kTbNaOH1QzZs49XxKCK_w74O1pRSQgbn0jx4ChZzhxXuPYga1Polfu6Oqp7xROT5OBA"

SLEEP_BETWEEN_CALLS = 1

os.makedirs("./db", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

with open("./db/market_code.json", "r", encoding="utf-8") as f:
    STOCKS = json.load(f)


def call_api(iscd: str):
    """특정 종목코드(iscd)를 한 번 호출하고, 성공 시 현재가 레코드를 반환"""
    logging.info("API 호출 시작 (종목코드=%s)", iscd)

    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST01010100",
    }

    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": iscd,
    }

    response = requests.get(API_URL, headers=headers, params=params, timeout=10)

    logging.info("HTTP status=%s", response.status_code)
    logging.info("응답 원문=%s", response.text)

    try:
        data = response.json()
    except Exception:
        logging.exception("JSON 파싱 실패")
        data = None

    rt_cd = data.get("rt_cd") if isinstance(data, dict) else None
    msg_cd = data.get("msg_cd") if isinstance(data, dict) else None
    msg1 = data.get("msg1") if isinstance(data, dict) else None

    logging.info("rt_cd=%s, msg_cd=%s, msg1=%s", rt_cd, msg_cd, msg1)

    debug_record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "iscd": iscd,
        "http_status": response.status_code,
        "rt_cd": rt_cd,
        "msg_cd": msg_cd,
        "msg1": msg1,
        "raw_response": response.text,
    }

    # 디버그용 로그(JSONL 유지)
    with open("api_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(debug_record, ensure_ascii=False) + "\n")

    # 실패면 None 리턴
    if not (response.status_code == 200 and rt_cd == "0"):
        logging.warning("⚠ 비정상 응답 (iscd=%s), 상세 내용은 api_log.jsonl 참고", iscd)
        return None

    # 성공이면 현재가만 추출
    try:
        stck_prpr = data["output"]["stck_prpr"]
    except Exception:
        stck_prpr = None

    success_record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "iscd": iscd,
        "stck_prpr": stck_prpr,
    }

    logging.info("✅ 현재가 조회 성공 (종목=%s, 현재가=%s)", iscd, stck_prpr)
    return success_record


def main():
    items = list(STOCKS.items())[:2000]

    results = []  # JSON 배열이 될 리스트

    for name, info in items:
        code = info["code"]
        logging.info("이번에 호출할 종목: 이름=%s, 코드=%s", name, code)

        rec = call_api(code)
        if rec is not None:
            results.append(rec)

        logging.info("다음 종목까지 %.1f초 대기", SLEEP_BETWEEN_CALLS)
        time.sleep(SLEEP_BETWEEN_CALLS)

    # 여기서 한 번에 JSON 배열로 저장
    with open("./db/all_prices.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logging.info("📁 all_prices.json에 %d개 레코드(JSON 배열) 저장 완료", len(results))


if __name__ == "__main__":
    main()
