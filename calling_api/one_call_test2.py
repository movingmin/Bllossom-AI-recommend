import requests
import json

url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price"

headers = {
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6ImFhODc0MmQ3LTcxMWYtNDM5Ni04YjE2LTYwMzZiMWRjZDU4MSIsInByZHRfY2QiOiIiLCJpc3MiOiJ1bm9ndyIsImV4cCI6MTc2MzExNTE5OCwiaWF0IjoxNzYzMDI4Nzk4LCJqdGkiOiJQU2ZLRUVtWVdobU9ObUh1VE9HeEtmRGN1ZTROc1ZDZU1KWkUifQ.AUuugyfIxsXoUv6OZ2bFWwMErXv40CSN1SOFSUOa3HP7j02drpltvU0edS6Lk5Yyhvdlb-WVMhOD1JR6vXaqHg",
    "appkey": "PSfKEEmYWhmONmHuTOGxKfDcue4NsVCeMJZE",
    "appkey": "PSfKEEmYWhmONmHuTOGxKfDcue4NsVCeMJZE",
    "appsecret": "VSXnfPwJdEW81zQV5A6Giwf+Plq0czrO/9mMrdgdgwcN7Mds5ah/lILSNF9M/JnO4bleBmkcQEPTP109I6PZ4ru/DhZ55r/mTYg9jLfsBPvEJ/URyb4dGEYaNq2CoJeGEmViRzYOboVFhUCHfDI49L2aHs2Ky3U44TzP988h2I7HfyPK8MU=",
    "tr_id": "FHKST01010100",
    "custtype": "P",
}

params = {
    "fid_cond_mrkt_div_code": "J",
    "fid_input_iscd": "005930",
}

# 필터링할 필드 목록
fields = [
    "stck_prpr",          # 현재가
    "rprs_mrkt_kor_name", # 시장 이름
    "bstp_kor_isnm",      # 업종명
    "stck_oprc",          # 시가
    "stck_hgpr",          # 고가
    "stck_lwpr",          # 저가
    "stck_mxpr",          # 상한가
    "stck_llam",          # 하한가
    "stck_sdpr"           # 기준가
]

response = requests.get(url, headers=headers, params=params)
data = response.json().get("output", {})

# 원하는 필드만 추출
filtered = {key: data.get(key) for key in fields}

print(json.dumps(filtered, indent=4, ensure_ascii=False))