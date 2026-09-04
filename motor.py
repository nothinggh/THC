import os
import random
import sqlite3
import time

# 1. 설정 정보
DB_DIR = r"C:\Users\user\work\middleware\THC"
DB_PATH = os.path.join(DB_DIR, "sensor_data.db")

# 2. 저장 디렉토리 생성
os.makedirs(DB_DIR, exist_ok=True)


# 3. 데이터베이스 및 테이블 초기화
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 모터 로그 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS motor_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            angle INTEGER,
            direction TEXT
        )
    """)

    conn.commit()
    conn.close()


# 4. 모터 데이터 생성 함수
def generate_motor_data():
    """0도 ~ 180도 사이의 각도 및 방향(CW/CCW) 데이터를 생성합니다."""
    angle = random.randint(0, 180)
    direction = random.choice(["CW", "CCW"])  # CW: 시계 방향, CCW: 반시계 방향
    return angle, direction


# 5. 시뮬레이션 실행 메인 루프
def main():
    init_db()
    print(f"DB 저장 경로: {DB_PATH}")
    print("모터 시뮬레이션을 시작합니다. (종료하려면 Ctrl+C를 누르세요)\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        while True:
            angle, direction = generate_motor_data()
            cursor.execute(
                "INSERT INTO motor_log (angle, direction) VALUES (?, ?)",
                (angle, direction),
            )
            conn.commit()

            print(f"[모터 구동] 각도: {angle}° | 방향: {direction}")

            # 0.5초 ~ 1.5초 사이 무작위 대기
            time.sleep(random.uniform(0.5, 1.5))

    except KeyboardInterrupt:
        print("\n시뮬레이터를 종료합니다.")
    finally:
        conn.close()
        print("DB 연결 종료 완료.")


if __name__ == "__main__":
    main()