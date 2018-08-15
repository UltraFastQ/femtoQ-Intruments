#include <Stepper.h>


const int StepPerRev = 400;

Stepper myStepper(StepPerRev, 9, 10, 11, 12);

int Lw_Pin = A0;
int H_Pin = A1;
int i = 0;
int j = 0;
long Step;
long TotStep;
char Side;
long Step2;
byte BYTES;
long  TotStep2;

void setup() {
  //put your setup code here, to run once:
  Serial.begin(9600);
  myStepper.setSpeed(20);
  pinMode(Lw_Pin, INPUT_PULLUP);
  pinMode(H_Pin,INPUT_PULLUP);
}

void loop() {

  if (Serial.available() > 0){
    Side = Serial.read();
    if (Side == 102){
      TotStep2 = 0;
      while (Serial.available() > 0) {
      Step = Serial.read();
      TotStep2 = TotStep2 + Step;
      }
      myStepper.step(-TotStep2);
      TotStep = TotStep + TotStep2;
      delay(100);
    }
    else if (Side == 114){
      myStepper.step(TotStep);
      delay(100);
      while (Serial.available() > 0) {
      Step = Serial.read();
      TotStep = TotStep - Step;

      }
    }
  }

  delay(500);
}
