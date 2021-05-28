"""

Monochromator - Contrôler un monochromateur.

Par Émile Jetzer
Basé sur un programme par Nicolas Perron
"""

from tkinter import messagebox

# Manipulation de données
from pathlib import Path

from .utils import Référence, Arduino


class MonoChrom:
    """Interface de contrôle d'un monochromateur."""

    def __init__(self,
                 arduino: Arduino = None,
                 référence: Référence = None,
                 longueur_de_calibration: float = 800.0,
                 mainf=None):
        if arduino is None or isinstance(arduino, str):
            arduino = Arduino(arduino)

        self.arduino: Arduino = arduino

        if référence is None:
            référence = 'ref.xlsx'

        if isinstance(référence, (str, Path)):
            référence = Référence(référence)

        self.référence: Référence = référence

        self.mainf = mainf

        self.longueur_donde: float = longueur_de_calibration
        self.longueur_de_calibration: float = longueur_de_calibration
        self.direction: int = 0
        self.hystérésie: int = 32  # Obtenu expérimentalement

    # Méthodes de compatibilité avec l'interface existante

    def connect(self, exp_dependencies: bool = False):
        self.arduino.connecter()
        if exp_dependencies:
            experiments = self.mainf.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options("Monochrom")

    def déconnecter(self):
        self.roll_dial(self.longueur_de_calibration)
        self.arduino.déconnecter()

    def bouger(self, nombre_de_pas: int, direction: int):
        if direction and (self.direction / direction == -1):
            nombre_de_pas += self.hystérésie
        self.direction = direction

        self.arduino.écrire(f"{nombre_de_pas}\t{direction}")
        while not self.arduino.connexion.in_waiting:
            pass
        limites = self.arduino.lire()
        diff = [int(i) for i in limites.split("\t")][1]

        if diff:
            messagebox.showinfo(
                'Too far!',
                'The dial is going too far one way! The optical switches were awakened!'
            )
        return diff

    def roll_dial(self, longueur_donde: float) -> int:
        pas, direction = self.référence.pas_à_faire(
            self.longueur_donde, longueur_donde)
        self.longueur_donde = longueur_donde

        return self.bouger(pas, direction)

    def calibrate(self,
                  spectro,
                  variable):
        if not spectro:
            messagebox.showinfo(
                title="Error", message="There is no spectrometer connected."
            )
            return
        if not self.arduino:
            messagebox.showinfo(
                title="Error", message="The monochromator is not connected."
            )

        response = messagebox.askyesno(
            title="Visibility", message="Is the spectrum visible by the spectro?"
        )

        # Ignorer une réponse positive
        if response == "no":
            message = f'Is the dial under {self.longueur_de_calibration/2}?'
            side = messagebox.askyesno(
                title="Side", message=message)

            if side == "yes":
                self.roll_dial(200)
            elif side == "no":
                self.roll_dial(-200)

        def màj_pos(spectro):
            intensités = spectro.intensities()
            longueurs_donde = spectro.wavelengths()
            intensité_max = max(intensités[2:])
            positions = [i for i, j in enumerate(
                intensités) if j == intensité_max]
            return longueurs_donde[positions[0]]

        self.longueur_donde = màj_pos(spectro)
        décalage = self.longueur_de_calibration - self.longueur_donde
        while abs(décalage) > 0.5:
            self.référence.df.longueur = self.référence.df.longueur - décalage
            self.roll_dial(self.longueur_de_calibration)
            self.longueur_donde = màj_pos(spectro)
            décalage = self.longueur_de_calibration - self.longueur_donde

        variable.set(self.longueur_donde)
        self.référence.sauvegarder()
        messagebox.showinfo(
            title="Success", message="The monochromator is calibrated")

    def __enter__(self):
        self.connect()

    def __exit__(self, *e):
        self.déconnecter()


if __name__ == "__main__":
    from serial.tools.list_ports import comports

    ports = comports()
    for i, p in enumerate(ports):
        print(f"[{i}] {p.device} {p.description}")
    port = ports[int(input("Port>"))].device

    with MonoChrom(port, 'ref.xlsx') as mc:
        a = input("Longueur d'onde: ")
        while a:
            mc.roll_dial(int(a))
            a = input("Longueur d'onde: ")
