"""
Monochromateur.py - Contrôler un monochromateur.

Par Émile Jetzer
Basé sur un programme par Nicolas Perron
"""

import serial, time
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
        self.df = pd.read_excel(chemin, sheet_name='cal', usecols=[
                                'cadran', 'longueur', 'moteur'])
        
        interpolateur = lambda x, y: interp1d(x, y, fill_value='extrapolate', bounds_error=False)
        self._pas_moteur = interpolateur(self.df.longueur, self.df.moteur)

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
    
    def pas_à_faire(self, départ: float, fin: float):
        pas = int(self._pas_moteur(fin) - self._pas_moteur(départ))
        return abs(pas), np.sign(pas)


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
        self.connexion.write(bytes(octets, encoding='utf-8'))
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
        
        return str(self.connexion.read(caractères), encoding='utf-8')

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
        self.longueur_donde: float = 0

        self.direction: int = 0
        self.fini: bool = True
        self.hystérésie: float = 28  # Obtenu expérimentalement

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
    
    def déconnecter(self):
        self.aller_a_longueur_donde(0)
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
        if direction and (self.direction/direction == -1):
            nombre_de_pas += self.hystérésie
        self.direction = direction
        
        self.arduino.écrire(f'{nombre_de_pas}\t{direction}')
        while not self.arduino.connexion.in_waiting:
            pass
        limites = self.arduino.lire()
        t, diff = [int(i) for i in limites.split('\t')]
        
        return diff

    def aller_a_longueur_donde(self, longueur_donde: float) -> int:
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
        pas, direction = self.référence.pas_à_faire(self.longueur_donde, longueur_donde)
        self.longueur_donde = longueur_donde

        return self.bouger(pas, direction)


if __name__ == '__main__':
    ref = Référence('ref.xlsx')

    ports = comports()
    for i, p in enumerate(ports):
        print(f'[{i}] {p.device} {p.description}')
    port = ports[int(input('Port>'))].device

    with Arduino(port) as arduino:
        mc = Monochromateur(arduino, ref)
        mc.connecter()
        
        a = input('Longueur d\'onde: ')
        while a:
            mc.aller_a_longueur_donde(int(a))
            a = input('Longueur d\'onde: ')
        
        mc.déconnecter()
