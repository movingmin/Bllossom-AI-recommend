# token_manager.py
import os
import requests
import json
import time

APP_KEY = "PSfKEEmYWhmONmHuTOGxKfDcue4NsVCeMJZE"
APP_SECRET = "VSXnfPwJdEW81zQV5A6Giwf+Plq0czrO/9mMrdgdgwcN7Mds5ah/lILSNF9M/JnO4bleBmkcQEPTP109I6PZ4ru/DhZ55r/mTYg9jLfsBPvEJ/URyb4dGEYaNq2CoJeGEmViRzYOboVFhUCHfDI49L2aHs2Ky3U44TzP988h2I7HfyPK8MU="


TOKEN_URL = "https://openapivts.koreainvestment.com:29443/oauth2/tokenP"

# token_manager.py 파일이 있는 폴더에 저장되게 고정 (선택사항)
BASE_DIR = os.path.dirname(__file__)
TOKEN_FILE = os.path.join(BASE_DIR, "access_token.json")


def get_new_token():
    data = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }

    response = requests.post(TOKEN_URL, json=data)

    try:
        res = response.json()
    except Exception:
        print("JSON 파싱 실패")
        print(response.text)
        raise

    print("토큰 발급 응답:", res)

    if "access_token" not in res:
        raise KeyError(f"access_token 없음. 응답 내용: {res}")

    access_token = res["access_token"]
    expires_in = int(res.get("expires_in", 0))

    token_data = {
        "access_token": access_token,
        "expires_at": time.time() + expires_in,
    }

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(token_data, f)

    print("새 토큰 발급 & 저장 완료:", TOKEN_FILE)
    return access_token


def load_token():
    """토큰 파일 로드 + 만료/오류 확인 + 자동 재발급"""

    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token_data = json.load(f)
    except FileNotFoundError:
        print("토큰 파일 없음 → 새 토큰 발급")
        return get_new_token()
    except json.JSONDecodeError:
        print("토큰 파일이 깨졌음(JSONDecodeError) → 새 토큰 발급")
        return get_new_token()

    access_token = token_data.get("access_token")
    expires_at = token_data.get("expires_at")

    # access_token 없거나 expires_at 이상하면 새로 발급
    if not access_token or not isinstance(expires_at, (int, float)):
        print("토큰 데이터 형식 이상 → 새 토큰 발급")
        return get_new_token()

    # 만료 1시간 전이면 갱신
    if time.time() >= expires_at - 3600:
        print("토큰 만료 임박 → 새 토큰 발급")
        return get_new_token()

    print("기존 토큰 사용 (아직 유효)")
    return access_token


if __name__ == "__main__":
    get_new_token()
