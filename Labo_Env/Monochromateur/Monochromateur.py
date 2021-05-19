"""
Monochromateur.py - Contrôler un monochromateur.

Par Émile Jetzer
Basé sur un programme par Nicolas Perron
"""

import serial
import time
from serial.tools.list_ports import comports
from tkinter import messagebox
from pathlib import Path
import pandas as pd
from scipy.interpolate import interp1d
import numpy as np


class Référence:
    """Interface d'interpolation à partir d'un tableau de données de \
référence."""

    def __init__(self, chemin: Path):
        """
        Interface d'interpolation à partir d'un tableau de données de \
référence.

        Parameters
        ----------
        chemin : Path
            Chemin du fichier excel contenant les données de référence. \
Le programme cherche la feuille cal, et utilise les colonnes cadran & longueur.

        Returns
        -------
        None.

        """
        self.chemin = chemin
        self.df = pd.read_excel(
            chemin, sheet_name="cal", usecols=["cadran", "longueur", "moteur"]
        )

    def __interpolateur(self, x, y):
        return interp1d(x, y, fill_value="extrapolate", bounds_error=False)

    def conversion(self, de: str, à: str):
        return self.__interpolateur(self.df[de], self.df[à])

    def pas_à_faire(self, départ: float, fin: float):
        fct = self.conversion("Longueur d'onde", "Pas moteurs")
        pas = int(fct(fin) - fct(départ))
        return abs(pas), np.sign(pas)

    def sauvegarder(self):
        self.df.to_excel(self.chemin, 'cal')


class Arduino:
    """Interface avec une carte Arduino."""

    def __init__(self, port: str, baudrate: int = 9600):
        """
        Interface avec une carte Arduino.

        Parameters
        ----------
        port : str
            Port série de la carte Arduino.
        baudrate : int, optional
            Débit de communication. The default is 9600.

        Returns
        -------
        None.

        """
        self.port = port
        self.baudrate = baudrate
        self.connexion = serial.Serial()

    def connecter(self):
        """
        Établir la connexion à la carte Arduino.

        Returns
        -------
        None.

        """
        if self.connexion.is_open:
            messagebox.showinfo(
                "Arduino déjà connecté",
                f"Il y a déjà une connexion au port {self.port}.",
            )
        else:
            self.connexion.port = self.port
            self.connexion.baudrate = self.baudrate
            self.connexion.open()

    def écrire(self, octets: str):
        """
        Écrire sur la carte Arduino.

        Parameters
        ----------
        octets : bytes
            Contenu à envoyer.

        Returns
        -------
        None.

        """
        self.connexion.write(bytes(octets, encoding="utf-8"))
        self.connexion.flush()

    def lire(self, caractères: int = None) -> str:
        """
        Lire une série de caractères de la carte Arduino.

        Parameters
        ----------
        caractères : int
            Nombre de caractères à lire.

        Returns
        -------
        bytes
            Caractères lus.

        """
        if caractères is None:
            caractères = self.connexion.in_waiting

        return str(self.connexion.read(caractères), encoding="utf-8")

    def déconnecter(self):
        """
        Fermer la connexion avec la carte Arduino.

        Returns
        -------
        None.

        """
        if self.connexion.is_open:
            self.connexion.close()

    def __enter__(self) -> "Arduino":
        """
        Gestionnaire de contexte, retourne l'objet Arduino.

        Returns
        -------
        Arduino
            L'objet lui-même.

        """
        return self

    def __exit__(self, *args) -> bool:
        """
        Gestionnaire de contexte, s'assure que la connexion est fermée.

        Parameters
        ----------
        *args : TYPE
            Arguments standards, ignorés ici.

        Returns
        -------
        bool
            False.

        """
        self.déconnecter()
        return False

    def __bool__(self):
        return self.connexion.is_open


class Monochromateur:
    """Interface de contrôle d'un monochromateur."""

    def __init__(self,
                 arduino: Arduino,
                 référence: Référence,
                 longueur_de_calibration: float = 800.0,
                 mainf=None):
        """
        Interface de contrôle d'un monochromateur.

        Parameters
        ----------
        arduino : Arduino
            Objet Arduino avec lequel communiquer.
        référence : Référence
            Données de référence.
        position_de_départ : float
            Affichage de départ du cadran.
        mainf : TYPE, optional
            Objet d'interface parent. The default is None.

        Returns
        -------
        None.

        """
        if isinstance(arduino, str):
            arduino = Arduino(arduino)

        self.arduino: Arduino = arduino

        if isinstance(référence, str) or isinstance(référence, Path):
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
        """
        Faire tourner le moteur de nombre_de_pas.

        Parameters
        ----------
        nombre_de_pas : int
            Nombre de pas à faire avec le moteur.

        Yields
        ------
        None.

        """
        if direction and (self.direction / direction == -1):
            nombre_de_pas += self.hystérésie
        self.direction = direction

        self.arduino.écrire(f"{nombre_de_pas}\t{direction}")
        while not self.arduino.connexion.in_waiting:
            pass
        limites = self.arduino.lire()
        t, diff = [int(i) for i in limites.split("\t")]

        if diff:
            messagebox.showinfo(
                'Too far!',
                'The dial is going too far one way! The optical switches were awakened!'
            )
        return diff

    def roll_dial(self, longueur_donde: float) -> int:
        """
        Amener le monochromateur à la longueur d'onde longueur_donde.

        Parameters
        ----------
        longueur_donde : float
            Longueur d'onde à atteindre.

        Returns
        -------
        Monochromateur
            Object de contrôle.

        """
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


if __name__ == "__main__":
    ref = Référence("ref.xlsx")

    ports = comports()
    for i, p in enumerate(ports):
        print(f"[{i}] {p.device} {p.description}")
    port = ports[int(input("Port>"))].device

    with Arduino(port) as arduino:
        mc = Monochromateur(arduino, ref)
        mc.connecter()

        a = input("Longueur d'onde: ")
        while a:
            mc.aller_a_longueur_donde(int(a))
            a = input("Longueur d'onde: ")

        mc.déconnecter()
