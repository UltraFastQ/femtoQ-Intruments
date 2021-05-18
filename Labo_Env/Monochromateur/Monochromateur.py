"""
Monochromateur.py - Contrôler un monochromateur.

Par Émile Jetzer
Basé sur un programme par Nicolas Perron
"""

import struct
import time
import serial
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
        self.df = pd.read_excel(chemin, sheet_name='cal', usecols=[
                                'cadran', 'longueur'])
        self._longueur_donde = interp1d(self.df.cadran, self.df.longueur)
        self._affichage_cadran = interp1d(self.df.longueur, self.df.cadran)

    def longueur_donde(self, cadran: float) -> float:
        """
        Calcule la longueur d'onde correspondant à l'affichage cadran.

        Parameters
        ----------
        cadran : float
            Affichage du cadran.

        Returns
        -------
        float
            Longueur d'onde correspondante.

        """
        return self._longueur_donde(cadran)

    def affichage_cadran(self, longueur: float) -> float:
        """
        Calcule l'affichage du cadran pour la longueur d'onde longueur.

        Parameters
        ----------
        longueur : float
            Longueur d'onde.

        Returns
        -------
        float
            Affichage du cadran.

        """
        return self._affichage_cadran(longueur)


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
                'Arduino déjà connecté',
                f'Il y a déjà une connexion au port {self.port}.')
        else:
            self.connexion.port = self.port
            self.connexion.baudrate = self.baudrate
            self.connexion.open()

    def écrire(self, octets: bytes):
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
        self.connexion.write(octets)

    def lire(self, caractères: int) -> bytes:
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
        return self.connexion.read(caractères)

    def déconnecter(self):
        """
        Fermer la connexion avec la carte Arduino.

        Returns
        -------
        None.

        """
        if self.connexion.is_open:
            self.connexion.close()

    def __enter__(self) -> 'Arduino':
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


class Monochromateur:
    """Interface de contrôle d'un monochromateur."""

    def __init__(self,
                 arduino: Arduino,
                 référence: Référence,
                 position_de_départ: float,
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
        self.arduino: Arduino = arduino
        self.mainf = mainf
        self.référence: Référence = référence
        self.position: float = position_de_départ

        self.côté: str = ''
        self.fini: bool = True
        self.facteur_de_pas: float = 2  # Obtenu expérimentalement
        self.décalage_hystérésie: float = 3  # Obtenu expérimentalement

    def connecter(self, exp_dependencies: bool = False) -> Arduino:
        """
        Établir la connexion avec le monochromateur.

        Parameters
        ----------
        exp_dependencies : bool, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        Arduino
            Objet Arduino avec lequel la connexion a été établie.

        """
        self.arduino.connecter()
        if exp_dependencies:
            experiments = self.mainf.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Monochrom')

        return self.arduino

    def régler_la_direction(self, direction: int) -> str:
        """
        Régler la direction du moteur du monochromateur.

        Parameters
        ----------
        direction : int
            Nombre négatif pour descendre, positif pour monter.

        Returns
        -------
        str
            Direction choisie, 'f' ou 'r'.

        """
        if self.arduino.connexion.is_open:
            côté: str = {1: 'f', 0: '', -1: 'r'}[np.sign(direction)]

            if self.côté is not côté:
                self.correction_hystérésie(côté)
                time.sleep(1)

            self.arduino.connexion.write(bytes(côté, encoding='utf-8'))

            self.côté = côté

        return côté

    def bouger(self, nombre_de_pas: int):
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
        if self.arduino.connexion.is_open:
            module_de_pas = nombre_de_pas % 255
            grands_pas = nombre_de_pas // 255

            # Envoyer les instructions au Arduino
            for i in range(grands_pas):
                self.arduino.connexion.write(struct.pack('>B', 255))
                # Permettre l'exécution de fonctions externes entre
                # les déplacements
                yield 255

            self.arduino.connexion.write(struct.pack('>B', module_de_pas))
            yield module_de_pas

    def aller_a_longueur_donde(self,
                               longueur_donde: float) -> 'Monochromateur':
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
        position_finale: float = self.référence.affichage_cadran(
            longueur_donde)
        différence: float = position_finale - self.position

        self.régler_la_direction(np.sign(différence))

        self.fini = False

        nombre_de_pas: int = round(abs(différence) * self.facteur_de_pas)

        # Envoyer les instructions au Arduino
        # Mettre à jour le compte de la position
        for pas in self.bouger(nombre_de_pas):
            self.position += np.sign(différence) * 255 / self.facteur_de_pas

        self.fini = True

        return self

    def correction_hystérésie(self, côté: str) -> 'Monochromateur':
        """
        Corriger pour l'hystérésie du moteur lors d'un changement de direction.

        Parameters
        ----------
        côté : str
            Nouveau côté.

        Returns
        -------
        Monochromateur
            Objet de contrôle.

        """
        if self.arduino.is_open:
            self.arduino.connexion.write(bytes(côté, encoding='utf-8'))
            self.bouger(self.décalage_hystérésie)

        return self


if __name__ == '__main__':
    ref = Référence('ref.xlsx')

    ports = serial.tools.list_ports.comports()
    for i, p in enumerate(ports):
        print(f'[{i}] {p.device} {p.description}')
    port = ports[int(input('Port>'))]

    with Arduino(port) as arduino:
        mc = Monochromateur(arduino, ref, 1500)
