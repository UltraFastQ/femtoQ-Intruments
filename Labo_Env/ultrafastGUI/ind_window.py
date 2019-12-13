import tkinter as tk
from Main_Frame import ZurichFrame

root = tk.Tk()
f1 = ZurichFrame(root)
f1.grid(column=0, row=0, sticky='nsew')

root.mainloop()

