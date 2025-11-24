from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import time
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_token_script():
    script_path = os.path.join(BASE_DIR, "token_manager.py")
    subprocess.run([sys.executable, script_path])
    print("토큰 갱신 스크립트 실행 완료")

def run_price_script():
    script_path = os.path.join(BASE_DIR, "full_call.py")
    subprocess.run([sys.executable, script_path])
    print("시세 갱신 스크립트 실행 완료")


scheduler = BackgroundScheduler()
scheduler.add_job(run_token_script, 'interval', minutes=1200, id="token_job")  # 20시간마다 실행
scheduler.add_job(run_price_script, 'interval', minutes=120, id="price_job")
scheduler.start()

print("스케줄러 시작됨...(토큰: 20시간 / 시세: 2시간마다)")

# 스케줄러 유지
while True:
    time.sleep(1)
