import requests
import json

url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price"

headers = {
    "authorization": f"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6ImFhODc0MmQ3LTcxMWYtNDM5Ni04YjE2LTYwMzZiMWRjZDU4MSIsInByZHRfY2QiOiIiLCJpc3MiOiJ1bm9ndyIsImV4cCI6MTc2MzExNTE5OCwiaWF0IjoxNzYzMDI4Nzk4LCJqdGkiOiJQU2ZLRUVtWVdobU9ObUh1VE9HeEtmRGN1ZTROc1ZDZU1KWkUifQ.AUuugyfIxsXoUv6OZ2bFWwMErXv40CSN1SOFSUOa3HP7j02drpltvU0edS6Lk5Yyhvdlb-WVMhOD1JR6vXaqHg",
    "appkey": "PSfKEEmYWhmONmHuTOGxKfDcue4NsVCeMJZE",
    "appsecret": "VSXnfPwJdEW81zQV5A6Giwf+Plq0czrO/9mMrdgdgwcN7Mds5ah/lILSNF9M/JnO4bleBmkcQEPTP109I6PZ4ru/DhZ55r/mTYg9jLfsBPvEJ/URyb4dGEYaNq2CoJeGEmViRzYOboVFhUCHfDI49L2aHs2Ky3U44TzP988h2I7HfyPK8MU=",
    "tr_id": "FHKST01010100",  # 실제 문서/포스트맨과 동일하게
    "custtype": "P",  # 개인이면 P, 법인이면 B (문서 확인)
}

params = {
    "fid_cond_mrkt_div_code": "J",
    "fid_input_iscd": "005930",
}

response = requests.get(url, headers=headers, params=params)

print("status:", response.status_code)
print("body:")
try:
    print("json:", json.dumps(response.json(), indent=4, ensure_ascii=False))
    
except json.JSONDecodeError:
    print("text:", response.text)