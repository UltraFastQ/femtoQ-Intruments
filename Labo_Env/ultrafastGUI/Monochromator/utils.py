#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 19 21:03:47 2021

@author: emilejetzer
"""

from pathlib import Path
from scipy.interpolate import interp1d

import serial
import pandas as pd
import numpy as np
import tkinter as tk


class Référence:
    """Interface d'interpolation à partir d'un tableau de données de \
référence."""

    def __init__(self, chemin: Path = 'ref.xlsx'):
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

    def __init__(self, port: str = None, baudrate: int = 9600, mainf=None):
        self.baudrate = baudrate
        self.connexion = serial.Serial()
        self.mainf = mainf

        if port is None:
            self.demander_port()
        else:
            self.port = port

    def demander_port(self):
        from serial.tools.list_ports import comports

        fenêtre = tk.Toplevel(self.mainf)
        fenêtre.geometry('250x250')

        ports = [p.device for p in comports()]

        tk.Label(fenêtre, text='Quel port série pour le monochromateur?').pack()
        var_port = tk.StringVar(fenêtre, ports[0])
        tk.OptionMenu(fenêtre, var_port, *ports).pack()

        def trace(*args):
            self.port = var_port.get()

        var_port.trace('w', trace)


    def connecter(self):
        if self.connexion.is_open:
            tk.messagebox.showinfo(
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
