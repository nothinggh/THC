import os
import re
import sqlite3
import time
import serial

# --- 설정 변수 ---
SERIAL_PORT = "COM14"
BAUD_RATE = 115200

# DB 저장 폴더 및 파일 경로 설정
DB_DIR = r"C:\Users\user\work\middleware\THC"
DB_FILE = os.path.join(DB_DIR, "sensor_data.db")


def init_db():
    """DB 폴더 및 테이블 생성 함수"""
    # 저장 폴더가 없으면 자동 생성
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print(f"폴더 생성 완료: {DB_DIR}")

    # DB 연결 및 테이블 생성
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # cds_data 테이블 생성 (id, 수신시간, cds_value)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cds_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
            cds_value INTEGER
        )
    """
    )

    conn.commit()
    conn.close()
    print(f"DB 준비 완료: {DB_FILE}")


def main():
    init_db()

    try:
        # 시리얼 포트 연결
        py_serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
        print(f"시리얼 포트 연결 성공: {SERIAL_PORT} ({BAUD_RATE} bps)")
        time.sleep(2)  # 아두이노 리셋 대기

        while True:
            if py_serial.in_waiting > 0:
                # 시리얼 한 줄 읽기 ("CDS : 512\r\n" 형식)
                raw_line = (
                    py_serial.readline().decode("utf-8", errors="ignore").strip()
                )

                if raw_line:
                    # 정규표현식을 사용해 숫자(CDS 데이터)만 추출
                    numbers = re.findall(r"\d+", raw_line)

                    if numbers:
                        cds_value = int(numbers[0])

                        # DB에 수신 데이터 저장
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO cds_log (cds_value) VALUES (?)",
                            (cds_value,),
                        )
                        conn.commit()
                        conn.close()

                        print(f"[DB 저장 성공] CDS 값: {cds_value}")

    except serial.SerialException as e:
        print(f"시리얼 포트 연결 오류: {e}")
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    finally:
        if "py_serial" in locals() and py_serial.is_open:
            py_serial.close()


if __name__ == "__main__":
    main()