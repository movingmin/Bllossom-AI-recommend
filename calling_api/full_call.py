import time
import requests
import logging
import json

# ===== 설정 부분 =====
# 모의투자 서버
URL_BASE = "https://openapivts.koreainvestment.com:29443"
PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"
API_URL = URL_BASE + PATH

APP_KEY = "PSfKEEmYWhmONmHuTOGxKfDcue4NsVCeMJZE"
APP_SECRET = "VSXnfPwJdEW81zQV5A6Giwf+Plq0czrO/9mMrdgdgwcN7Mds5ah/lILSNF9M/JnO4bleBmkcQEPTP109I6PZ4ru/DhZ55r/mTYg9jLfsBPvEJ/URyb4dGEYaNq2CoJeGEmViRzYOboVFhUCHfDI49L2aHs2Ky3U44TzP988h2I7HfyPK8MU="
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6ImU4ODUxMmZhLTYzNDUtNDY1OC04NWM5LTU3Nzc2OTMyMzE0NCIsInByZHRfY2QiOiIiLCJpc3MiOiJ1bm9ndyIsImV4cCI6MTc2MzcxNDI3MywiaWF0IjoxNzYzNjI3ODczLCJqdGkiOiJQU2ZLRUVtWVdobU9ObUh1VE9HeEtmRGN1ZTROc1ZDZU1KWkUifQ.qTLwTB2z3u7SyhrRi54kTbNaOH1QzZs49XxKCK_w74O1pRSQgbn0jx4ChZzhxXuPYga1Polfu6Oqp7xROT5OBA"
# 종목 사이 대기 시간(초)
SLEEP_BETWEEN_CALLS = 1

# ===== 로깅 설정 =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# codes.json: { "삼성전자": {"code": "005930", "market": "P"}, ... } 형태 가정
with open("codes.json", "r", encoding="utf-8") as f:
    STOCKS = json.load(f)


def call_api(iscd: str):
    """특정 종목코드(iscd)를 한 번 호출"""
    logging.info("API 호출 시작 (종목코드=%s)", iscd)

    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST01010100",  # 국내주식 현재가 TR ID
    }

    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": iscd,
    }

    response = requests.get(API_URL, headers=headers, params=params, timeout=10)

    logging.info("HTTP status=%s", response.status_code)
    logging.info("응답 원문=%s", response.text)

    # JSON 파싱 시도
    try:
        data = response.json()
    except Exception:
        logging.exception("JSON 파싱 실패")
        data = None

    rt_cd = None
    msg_cd = None
    msg1 = None

    if isinstance(data, dict):
        rt_cd = data.get("rt_cd")
        msg_cd = data.get("msg_cd")
        msg1 = data.get("msg1")

    logging.info("rt_cd=%s, msg_cd=%s, msg1=%s", rt_cd, msg_cd, msg1)

    # ===== 디버그용: 성공/실패 상관없이 전부 기록 =====
    debug_record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "iscd": iscd,
        "http_status": response.status_code,
        "rt_cd": rt_cd,
        "msg_cd": msg_cd,
        "msg1": msg1,
        "raw_response": response.text,
    }

    with open("api_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(debug_record, ensure_ascii=False) + "\n")
    
    if response.status_code == 200 and rt_cd == "0":

        # stck_prpr(현재가)만 추출
        stck_prpr = None
        try:
            stck_prpr = data["output"]["stck_prpr"]   # <<< ⭐ 현재가만 추출
        except Exception:
            pass

        # stck_prpr만 저장하도록 변경
        success_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "iscd": iscd,
            "stck_prpr": stck_prpr,  # <<< ⭐ 현재가만 저장
        }

        with open("api.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(success_record, ensure_ascii=False) + "\n")

        logging.info("✅ api.json에 [%s] 현재가 %s 저장 완료", iscd, stck_prpr)
    else:
        logging.warning("⚠ 비정상 응답 (iscd=%s), 상세 내용은 api_log.jsonl 참고", iscd)


def main():
    """앞 5개 종목만 한 번씩 호출 (테스트용)"""
    items = list(STOCKS.items())[:2000]

    for name, info in items:
        code = info["code"]  # "005930" 같은 6자리 코드
        logging.info("이번에 호출할 종목: 이름=%s, 코드=%s", name, code)

        call_api(code)

        logging.info("다음 종목까지 %.1f초 대기", SLEEP_BETWEEN_CALLS)
        time.sleep(SLEEP_BETWEEN_CALLS)


if __name__ == "__main__":
    main()
