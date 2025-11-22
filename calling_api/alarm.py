from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import time

def run_token_script():
    # 실행하고 싶은 py 파일 경로
    subprocess.run(["python", "token_manager.py"])
    print("토큰 갱신 스크립트 실행 완료")

def run_price_script():
    # 실행하고 싶은 py 파일 경로
    subprocess.run(["python", "full_call.py"])
    print("시세 갱신 스크립트 실행 완료")


scheduler = BackgroundScheduler()
scheduler.add_job(run_token_script, 'interval', minutes=3, id="token_job")  # 10초마다 실행

scheduler.add_job(run_price_script, 'interval', minutes=1, id="price_job")
scheduler.start()

print("스케줄러 시작됨...(토큰: 3분 / 시세: 1분마다)")

# 스케줄러 유지
while True:
    time.sleep(1)
