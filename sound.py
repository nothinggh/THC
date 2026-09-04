import os
import re
import sqlite3
import time
import serial

# 1. 설정 정보
SERIAL_PORT = "COM14"
BAUD_RATE = 115200  # 아두이노 Serial.begin(115200)과 일치하도록 설정
DB_DIR = r"C:\Users\user\work\middleware\THC"
DB_PATH = os.path.join(DB_DIR, "sensor_data.db")

# 2. 저장 디렉토리 생성
os.makedirs(DB_DIR, exist_ok=True)


# 3. 데이터베이스 및 테이블 초기화
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sound_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sound_value INTEGER,
            deviation INTEGER
        )
    """)
    conn.commit()
    conn.close()


# 4. 시리얼 수신 및 DB 저장 메인 루프
def main():
    init_db()
    print(f"DB 저장 경로: {DB_PATH}")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        print(f"시리얼 포트 연결 성공: {SERIAL_PORT} ({BAUD_RATE} bps)")
        time.sleep(2)  # 아두이노 리셋 대기
    except serial.SerialException as e:
        print(f"시리얼 포트 연결 실패: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 시리얼 문자열 정규식 파싱 패턴
    # 예시 입력: "소리 감지! 현재값: 610 (변화량: 60)"
    pattern = re.compile(r"현재값:\s*(\d+).*?변화량:\s*(\d+)")

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                # 정규식을 이용해 현재값과 변화량 숫자 추출
                match = pattern.search(line)
                if match:
                    sound_val = int(match.group(1))
                    deviation_val = int(match.group(2))

                    # DB 저장
                    cursor.execute(
                        "INSERT INTO sound_log (sound_value, deviation) VALUES (?, ?)",
                        (sound_val, deviation_val),
                    )
                    conn.commit()

                    print(
                        f"[DB 저장 완료] 소리 감지! - 센서값: {sound_val} | 변화량: {deviation_val}"
                    )

    except KeyboardInterrupt:
        print("\n수집을 중단합니다.")
    finally:
        ser.close()
        conn.close()
        print("연결 종료 완료.")


if __name__ == "__main__":
    main()