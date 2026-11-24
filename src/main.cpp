#include <Arduino.h>

static unsigned long compteur = 0;

void setup() {
  pinMode(LED_GREEN, OUTPUT);
  Serial.begin(115200);
  Serial.println("Bonjour STeaMi !");
}

void loop() {
  digitalWrite(LED_GREEN, HIGH);
  delay(500);
  digitalWrite(LED_GREEN, LOW);
  delay(500);
  Serial.println(compteur++);
}
