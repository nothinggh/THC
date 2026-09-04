import re
import sqlite3
import time
import serial

# --------------------------------------------------
# 설정
# --------------------------------------------------

SERIAL_PORT = "COM14"
BAUD_RATE = 115200

DB_FILE = r"C:\Users\user\work\middleware\THC\sensor_data.db"

# --------------------------------------------------
# 데이터베이스 연결
# --------------------------------------------------

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 테이블 자동 생성ls

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (
        strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
    )
)
"""
)
conn.commit()


# --------------------------------------------------
# Arduino Serial 연결
# --------------------------------------------------

ser = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)

# Arduino 재시작 대기
time.sleep(2)

print("Temperature / Humidity Collector Started")
print(f"Serial Port : {SERIAL_PORT}")
print(f"Database    : {DB_FILE}")
print("------------------------------------------")


# --------------------------------------------------
# 데이터 수집
# --------------------------------------------------

try:
    while True:
        # Arduino에서 한 줄 읽기
        line = ser.readline().decode("utf-8", errors="ignore").strip()

        # 빈 데이터는 무시
        if not line:
            continue

        print(f"수신: {line}")

        try:
            # 정규표현식을 사용하여 문자열 내부의 모든 숫자(소수점 포함) 추출
            # 예: "Temperature: 25.50[C] Humidity: 53.90[%]" -> ['25.50', '53.90']
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)

            # 온도와 습도 값이 모두 추출되었는지 확인
            if len(numbers) >= 2:
                temperature = float(numbers[0])
                humidity = float(numbers[1])

                # SQLite DB 저장
                cursor.execute(
                    """
                    INSERT INTO sensor_data (
                        temperature,
                        humidity
                    )
                    VALUES (?, ?)
                    """,
                    (temperature, humidity),
                )
                conn.commit()

                print(
                    f"저장 완료 -> "
                    f"Temperature: {temperature:.1f} C, "
                    f"Humidity: {humidity:.1f} %"
                )
            else:
                print(f"숫자 데이터를 추출하지 못함: {line}")

        except ValueError:
            print(f"숫자 변환 오류: {line}")

except KeyboardInterrupt:
    print("\n수집기를 종료합니다.")

finally:
    # Serial 및 DB 연결 종료
    ser.close()
    conn.close()