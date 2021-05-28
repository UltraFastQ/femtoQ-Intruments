/* Monochromateur.ino
   par Émile Jetzer
   jeudi 6 mai 2021
*/

#include "mc.h"

// Communication série
#define BAUD 9600

volatile char etat;
String commande;
int ms[4] = {9, 10, 11, 12};
int ls[2] = {A0, A1};
Monochromateur mc(ms, ls);

void setup() {
  Serial.begin(BAUD);

  delay(10);
}

void loop() {
  if (Serial.available() > 0) {
    int pas = Serial.parseInt();
    int dir = Serial.parseInt();
    mc.moteurs(pas, dir);
    Serial.println(String(millis()) + '\t' + String(mc.limites()));
    Serial.flush();
  }
}
