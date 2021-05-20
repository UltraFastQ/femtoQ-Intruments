#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 19 21:03:47 2021

@author: emilejetzer
"""

import serial
from pathlib import Path
import pandas as pd
from scipy.interpolate import interp1d
import numpy as np


class Référence:
    """Interface d'interpolation à partir d'un tableau de données de \
référence."""

    def __init__(self, chemin: Path):
        self.chemin = chemin
        self.df = pd.read_excel(
            chemin, sheet_name="cal", usecols=["cadran", "longueur", "moteur"]
        )

    def __interpolateur(self, x, y):
        return interp1d(x, y, fill_value="extrapolate", bounds_error=False)

    def __conversion(self, de: str, à: str):
        return self.__interpolateur(self.df[de], self.df[à])

    def pas_à_faire(self, départ: float, fin: float):
        fct = self.__conversion("Longueur d'onde", "Pas moteurs")
        pas = int(fct(fin) - fct(départ))
        return abs(pas), np.sign(pas)

    def sauvegarder(self):
        self.df.to_excel(self.chemin, 'cal')


class Arduino:
    """Interface avec une carte Arduino."""

    def __init__(self, port: str, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.connexion = serial.Serial()

    def connecter(self):
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
        self.connexion.write(bytes(octets, encoding="utf-8"))
        self.connexion.flush()

    def lire(self, caractères: int = None) -> str:
        if caractères is None:
            caractères = self.connexion.in_waiting

        return str(self.connexion.read(caractères), encoding="utf-8")

    def déconnecter(self):
        if self.connexion.is_open:
            self.connexion.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.déconnecter()

    def __bool__(self):
        return self.connexion.is_open
