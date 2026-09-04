const int SOUND_A0 = A0;
const int LED = 13;

// 1. 시리얼 모니터로 평소 조용할 때 출력을 확인한 후, 그 기준값을 입력하세요. (보통 500~520 근처)
const int BASE_VALUE = 550; 

// 2. 민감도 설정 (기준값에서 얼마나 변했을 때 소리로 볼 것인가)
// 숫자가 작을수록 작은 소리에도 반응합니다. (추천: 15~30)
const int SENSITIVITY = 50; 

void setup()
{
  Serial.begin(9600);
  pinMode(LED, OUTPUT);
}

void loop()
{
  int soundValue = analogRead(SOUND_A0);

  // 평소 기준값과의 차이(변화량) 계산
  int deviation = abs(soundValue - BASE_VALUE);

  // 설정한 민감도보다 변화가 크면 소리로 인지
  if (deviation > SENSITIVITY)
  {
    digitalWrite(LED, HIGH);
    Serial.print("소리 감지! 현재값: ");
    Serial.print(soundValue);
    Serial.print(" (변화량: ");
    Serial.print(deviation);
    Serial.println(")");
    
    delay(100); 
  }
  else
  {
    digitalWrite(LED, LOW);
  }

  delay(100);
}
