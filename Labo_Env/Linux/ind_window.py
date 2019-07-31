import tkinter as tk
from Main_Frame import Mono_Physics

root = tk.Tk()
f1 = Mono_Physics(root)
f1.grid(column=0, row=0, sticky='nsew')

root.mainloop()

