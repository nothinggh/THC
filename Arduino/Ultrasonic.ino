int pinGnd = 5;
int pinEcho = 4;
int pinTrigger = 3;
int pinVcc = 2;

void setup() {
  Serial.begin(115200);

  pinMode(pinGnd, OUTPUT);
  pinMode(pinVcc, OUTPUT);
  pinMode(pinTrigger, OUTPUT);
  pinMode(pinEcho, INPUT);
  digitalWrite(pinGnd, LOW);
  digitalWrite(pinVcc, HIGH);
}

void loop() {
  float fDuration, fDistance;

  digitalWrite(pinTrigger, HIGH);
  delayMicroseconds(10);
  digitalWrite(pinTrigger, LOW);

  fDuration = pulseIn(pinEcho, HIGH);
  Serial.println(fDuration);
  fDistance = ((float)(340 * fDuration)) / 10000 / 2;
  Serial.print(fDistance);
  Serial.println("cm");
  delay(500);
}
