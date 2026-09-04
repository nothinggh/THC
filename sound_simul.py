import os
import random
import sqlite3
import time

# 1. 설정 정보
DB_DIR = r"C:\Users\user\work\middleware\THC"
DB_PATH = os.path.join(DB_DIR, "sensor_data.db")

# 소리 센서 기준값 설정
BASE_VALUE = 550
SENSITIVITY = 50

# 2. 저장 디렉토리 생성
os.makedirs(DB_DIR, exist_ok=True)


# 3. 데이터베이스 및 테이블 초기화
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 소리 로그 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sound_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sound_value INTEGER,
            deviation INTEGER
        )
    """)

    # 거리 로그 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            duration_us REAL,
            distance_cm REAL
        )
    """)

    conn.commit()
    conn.close()


# 4. 랜덤 데이터 생성 함수
def generate_sound_data():
    """소리 감지 기준(SENSITIVITY)을 넘는 임의의 데이터를 생성합니다."""
    deviation = random.randint(SENSITIVITY + 1, 250)
    # 기준값(550)을 중심으로 Random +/- 적용
    sound_value = (
        BASE_VALUE + deviation
        if random.choice([True, False])
        else BASE_VALUE - deviation
    )
    return sound_value, deviation


def generate_distance_data():
    """2cm ~ 200cm 사이의 가상 초음파 거리 데이터를 생성합니다."""
    distance_cm = round(random.uniform(2.0, 200.0), 2)
    # 거리(cm) = (Duration * 340) / 10000 / 2 역산하여 Duration(us) 계산
    duration_us = round((distance_cm * 2 * 10000) / 340, 2)
    return duration_us, distance_cm


# 5. 시뮬레이션 실행 메인 루프
def main():
    init_db()
    print(f"DB 저장 경로: {DB_PATH}")
    print(
        "센서 시뮬레이션을 시작합니다. (종료하려면 Ctrl+C를 누르세요)\n"
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        while True:
            # 1. 소리 센서 이벤트 시뮬레이션 (40% 확률로 발생)
            if random.random() < 0.4:
                sound_val, deviation_val = generate_sound_data()
                cursor.execute(
                    "INSERT INTO sound_log (sound_value, deviation) VALUES (?, ?)",
                    (sound_val, deviation_val),
                )
                print(
                    f"[소리 감지] 센서값: {sound_val} | 변화량: {deviation_val}"
                )

            # 2. 초음파 거리 센서 이벤트 시뮬레이션 (60% 확률로 발생)
            if random.random() < 0.6:
                duration, distance = generate_distance_data()
                cursor.execute(
                    "INSERT INTO distance_logs (duration_us, distance_cm) VALUES (?, ?)",
                    (duration, distance),
                )
                print(
                    f"[거리 측정] Duration: {duration} us | Distance: {distance} cm"
                )

            conn.commit()

            # 0.5초 ~ 1.5초 사이 무작위 대기
            time.sleep(random.uniform(0.5, 1.5))

    except KeyboardInterrupt:
        print("\n시뮬레이터를 종료합니다.")
    finally:
        conn.close()
        print("DB 연결 종료 완료.")


if __name__ == "__main__":
    main()