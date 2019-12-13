from tkinter import messagebox
import time


class PMD_1008:
        
    def __init__(self):
        self.card = None

    def connect_card(self):
        import usb_1208LS as us
        self.card = us.usb_miniLAB()
        if self.card:    
            messagebox.showinfo(title='INFO', message='Red Lab connected')
        else:
            messagebox.showinfo(title='ERROR', message='No device found')

    def quick_measure(self, duree, file_name):
        import usb_1208LS as us
        
        if self.card == None :
           print('connect card')
        else :
            chan = 2
            gain = self.card.BP_1_00V

            values = np.zeros(0)
            x = np.zeros(0)

            start = time.time()

            while ((time.time() - start) < duree):
                values = np.append(values, self.card.AIn(chan, gain))
                x = np.append(x, time.time() - start)

            plt.plot(x, values)
            plt.show()
