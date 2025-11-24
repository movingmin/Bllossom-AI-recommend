# Web 페이지 제작 디렉터리

## 서버 실행
```
python manage.py runserver --noreload
```

# 외부 접속(배포) Cloudflare Tunnel
내 컴퓨터(로컬 서버)를 외부에서 접속할 수 있도록 **Cloudflare Tunnel**을 설정하는 방법

## 1. Cloudflare Tunnel (`cloudflared`) 다운로드

1.  [Cloudflare 다운로드 페이지](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/)에 접속.
2.  **Windows** 섹션에서 `cloudflared-windows-amd64.exe`를 다운로드합니다.
3.  다운로드한 파일의 이름을 입력하기 쉽게 `cloudflared-windows.exe`로 변경하고, 웹 폴더(`Web/`)에 넣어둘 것.

## 2. Django 설정 변경 (`settings.py`)
외부에서 접속하려면 Django가 해당 도메인을 허용해야 함.
1.  `Web/myproject/settings.py` 파일을 열고
2.  `ALLOWED_HOSTS` 설정을 찾아서 아래와 같이 변경.

```python
# Web/myproject/settings.py

# 모든 도메인 접속 허용
ALLOWED_HOSTS = ['*']
```
> **주의**: 보안을 위해 배포가 끝나면 다시 원래대로 돌려놓거나, 할당받은 Cloudflare 주소만 넣는 것이 좋음.

## 3. 서버 실행

먼저 Django 웹 서버를 실행해 둡니다. (이미 켜져 있다면 패스)

```bash
# 터미널 1
python manage.py runserver --noreload
```

## 4. Cloudflare Tunnel 실행

새로운 터미널(PowerShell 또는 CMD)을 열고, `cloudflared.exe`가 있는 폴더로 이동한 뒤 아래 명령어를 입력.

```bash
# 터미널 2 (cloudflared가 있는 경로에서)
./cloudflared-windows.exe tunnel --url http://localhost:8000
```

## 5. 접속 주소 확인

명령어를 실행하면 터미널에 여러 로그가 뜨는데, 그중 아래와 같은 형식의 URL을 찾기(네모박스 안에 있음).

```text
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
|  https://random-name-generated.trycloudflare.com                                           |
+--------------------------------------------------------------------------------------------+
```

*   위 `https://....trycloudflare.com` 주소를 통해 접속이 가능.
*   이 주소는 `cloudflared`를 끌 때까지만 유효하며, 다시 켜면 주소가 바뀜