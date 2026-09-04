import os
import sqlite3
import time
import serial

# 1. 설정 정보
SERIAL_PORT = "COM14"
BAUD_RATE = 115200
DB_DIR = r"C:\Users\user\work\middleware\THC"
DB_PATH = os.path.join(DB_DIR, "sensor_data.db")

# 2. 저장 디렉토리 생성
os.makedirs(DB_DIR, exist_ok=True)

# 3. 데이터베이스 초기화 및 테이블 생성
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            duration_us REAL,
            distance_cm REAL
        )
    """)
    conn.commit()
    conn.close()

# 4. 시리얼 수신 및 DB 저장 메인 루프
def main():
    init_db()
    print(f"DB 경로: {DB_PATH}")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        print(f"포트 연결 성공: {SERIAL_PORT}")
        time.sleep(2)  # 아두이노 리셋 대기
    except serial.SerialException as e:
        print(f"시리얼 포트 연결 실패: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    temp_duration = None  # fDuration 값 임시 저장

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                # 첫 번째 출력 (fDuration)
                if temp_duration is None:
                    try:
                        temp_duration = float(line)
                    except ValueError:
                        pass
                
                # 두 번째 출력 (fDistance + "cm")
                else:
                    if line.endswith("cm"):
                        try:
                            distance_str = line.replace("cm", "").strip()
                            distance_val = float(distance_str)

                            # DB에 저장
                            cursor.execute(
                                "INSERT INTO distance_log (duration_us, distance_cm) VALUES (?, ?)",
                                (temp_duration, distance_val)
                            )
                            conn.commit()
                            print(f"[저장 성공] Duration: {temp_duration} us | Distance: {distance_val} cm")

                        except ValueError:
                            print(f"[파싱 에러] 잘못된 데이터 형식: {line}")
                        
                        temp_duration = None  # 수신 상태 초기화

    except KeyboardInterrupt:
        print("\n수집을 중단합니다.")
    finally:
        ser.close()
        conn.close()
        print("연결 종료 완료.")

if __name__ == "__main__":
    main()