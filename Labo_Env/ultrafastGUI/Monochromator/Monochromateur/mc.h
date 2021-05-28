class Monochromateur {
  public:
    int ms[4];
    int ls[2];
    int etat_ms[4];
    int etat_ls[2];
    int pos = 0;
    int lim = 0;

    int sequence[4][4] = {{LOW, HIGH, HIGH, LOW},
                                {LOW, HIGH, LOW, HIGH},
                                {HIGH, LOW, LOW, HIGH},
                                {HIGH, LOW, HIGH, LOW}};
    int arret[4] = {LOW, LOW, LOW, LOW};
    int limite = 1000;

    void regler_bobines(int etat[4]);
    void moteurs(int pas, int dir);

    int limites(void);

    Monochromateur(int _ms[4], int _ls[2]);
};

Monochromateur::Monochromateur(int _ms[4], int _ls[2]) {
  for (int i = 0; i < 2; i++) {
    ls[i] = _ls[i];
    pinMode(ls[i], INPUT);
  }

  for (int i = 0; i < 4; i++) {
    ms[i] = _ms[i];
    pinMode(ms[i], OUTPUT);
  }
}

void Monochromateur::regler_bobines(int etat[4]) {
  for (int i = 0; i < 4; i++) {
     digitalWrite(ms[i], etat[i]);
  }
}

void Monochromateur::moteurs(int pas, int dir) {
  switch (dir) {
    case 1:
      lim = pos+pas;
      for (int i = pos; i < lim; i++) {
        regler_bobines(sequence[i % 4]);
        pos++;
        delay(5);
      }
      pos += pas;
      break;
    case -1:
      lim = pos+pas;
      for (int i = pos; i < lim; i++) {
        regler_bobines(sequence[3 - (i % 4)]);
        pos++;
        delay(5);
      }
      break;
    default:
      regler_bobines(arret);
  }
}

int Monochromateur::limites() {
  for ( int i = 0; i < 2; i++ ) {
    etat_ls[i] = analogRead(ls[i]);
  }

  return etat_ls[1] - etat_ls[0];
}
