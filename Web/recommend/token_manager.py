import sys
import os
from pathlib import Path

# calling_api 폴더를 sys.path에 추가하여 token_manager 모듈을 불러옵니다.
# 현재 파일: Web/recommend/token_manager.py
# 목표: calling_api/token_manager.py
# Web/recommend -> Web -> Root -> calling_api
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CALLING_API_DIR = BASE_DIR / "calling_api"

if str(CALLING_API_DIR) not in sys.path:
    sys.path.append(str(CALLING_API_DIR))

try:
    from token_manager import load_token, APP_KEY, APP_SECRET
except ImportError as e:
    print(f"Error importing token_manager from calling_api: {e}")
    raise e
