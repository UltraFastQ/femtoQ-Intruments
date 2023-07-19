import asyncio
import struct
import time
from pylab import *

import usb.core  # type: ignore

from yaqd_core import HasTurret, IsHomeable, HasLimits, HasPosition, IsDaemon


__all__ = ["HoribaMono"]


LANG_ID_US_ENGLISH = 0x409

# Identifiers of the product in USB spec
JOBIN_YVON_ID_VENDOR = 0xC9B
MICRO_HR_ID_PRODUCT = 0x100
IHR320_ID_PRODUCT = 0x101

# Parameters for ctrl_transfer
BM_REQUEST_TYPE = 0xB3
B_REQUEST_OUT = 0x40
B_REQUEST_IN = 0xC0

# wIndex values for USB commands
INITIALIZE = 0
SET_WAVELENGTH = 4
READ_WAVELENGTH = 2
SET_TURRET = 17
READ_TURRET = 16
SET_MIRROR = 41
READ_MIRROR = 40
SET_SLITWIDTH = 33
READ_SLITWIDTH = 32
IS_BUSY = 5


class HoribaMono(HasTurret, IsHomeable, HasLimits, HasPosition, IsDaemon):
    def __init__(self, name, config, config_filepath):
        # TODO: Support multiple monos on the same machine
        super().__init__(name, config, config_filepath)
        try:
            from usb.backend import libusb0  # type: ignore

            backend = libusb0.get_backend()
        except:
            # Fall back on default behavior if _anything_ goes wrong with specifing libusb0
            backend = None
        self._dev = usb.core.find(
            idVendor=JOBIN_YVON_ID_VENDOR, idProduct=IHR320_ID_PRODUCT, backend=backend
        )

        self._busy = True

        # Lie to the device that it speaks US English
        # Without this, the strings read from USB don't work
        self._dev._langids = (LANG_ID_US_ENGLISH,)
        self.description = ""#self._dev.product
        self.serial = ""#self._dev.serial_number
        self._gratings = config["gratings"]
        self._units = "nm"
        
        try:
            turret_i = loadtxt("C:/Users/Liom-admin/anaconda3/Lib/site-packages/yaqd_core/turret.txt",unpack=True)
        except:
            print("Manually check what is the ihr320's current grating;\n insert 0 for the 600 grooves/mm grating,\n 1 for the 150 grooves/mm grating or\n 2 for the 120 grooves/mm grating")
            turret_i = input("Grating index: ")
            my_file = open("C:/Users/Liom-admin/anaconda3/Lib/site-packages/yaqd_core/turret.txt", "w")
            my_file.write(f'{turret_i}')
            my_file.close()
            
        self._state["turret"] = list(self._gratings.keys())[int(turret_i)]
            
        self.home()
        
        self.set_position(100)
        self.set_front_entrance_slit(1)
        self.set_front_exit_slit(1)
        
    async def _reset_position(self):
        self.logger.debug("in reset_position")

        if self._busy:
            await self._not_busy_sig.wait()
        self.logger.debug(self._state["turret"])
        self._dev.ctrl_transfer(
            B_REQUEST_OUT,
            BM_REQUEST_TYPE,
            wIndex=SET_TURRET,
            data_or_wLength=struct.pack("<i", self._gratings[self._state["turret"]]["index"]),
        )
        self._busy = True
        await self._not_busy_sig.wait()
        self._state["hw_limits"] = (
            0.0,
            1580 * 1200 / self._gratings[self._state["turret"]]["lines_per_mm"],
        )
        #self.set_position(self._state["destination"])

    def home(self):
        # Send "Initialize command, which homes the motor"
        self._dev.ctrl_transfer(0x40, 0xB3, wValue=0, wIndex=0)
        loop = asyncio.get_event_loop()
        loop.create_task(self._reset_position())
        
        #self._state["turret"] = self.get_turret()
        
        delay = 35
        print(f'home: {delay} s')
        time.sleep(delay)
        print('home done')

    def set_turret(self, identifier):
        
        if identifier == 600:
            identifier = "grating 1; 600 lines per mm"
        if identifier == 150:
            identifier = "grating 2; 150 lines per mm"
        if identifier == 120:
            identifier = "grating 3; 120 lines per mm"
            
        self._busy = True
        
        self.logger.debug(self._state["turret"], identifier)
        if identifier != self._state["turret"]:
            
            if '120' in identifier and '600' in self._state["turret"]:
                delay = 70
            elif '150' in identifier and '120' in self._state["turret"]:
                delay = 70
            elif '600' in identifier and '150' in self._state["turret"]:
                delay = 70
            else:
                delay = 40
             
            message1 = 'changing grating'
            message2 = 'grating changed'
            modifyTurret = True
            
            if identifier == "grating 1; 600 lines per mm":
                turret_i = 0
            elif identifier == "grating 2; 150 lines per mm":
                turret_i = 1
            elif identifier == "grating 3; 120 lines per mm":
                turret_i = 2
            self._state["turret"] = identifier
            self._dev.ctrl_transfer(
            B_REQUEST_OUT,
            BM_REQUEST_TYPE,
            wIndex=SET_TURRET,
            data_or_wLength=struct.pack("<i", self._gratings[self._state["turret"]]["index"]),
        )
            
            loop = asyncio.get_event_loop()
            loop.create_task(self._reset_position())
            
        else:
            delay = 1
            message1 = 'grating already in correct position'
            message2 = ''
            modifyTurret = False
        
        print(f'{message1}: {delay} s')
        time.sleep(delay)
        print(message2)
        
        if modifyTurret:
            my_file = open("C:/Users/Liom-admin/anaconda3/Lib/site-packages/yaqd_core/turret.txt", "w")
            my_file.write(f'{turret_i}')
            my_file.close()
        
        time.sleep(1)
        self.set_position(self._state["destination"])

    def get_turret(self):
        return self._state["turret"]

    def get_turret_options(self):
        return list(self._gratings.keys())

    def _set_position(self, position):
        # Mono assumes 1200 lines/mm, adjust accordingly
        self.logger.debug(position)
        position = position * self._gratings[self._state["turret"]]["lines_per_mm"] / 1200.0
        self.logger.debug(position)
        self._dev.ctrl_transfer(
            B_REQUEST_OUT,
            BM_REQUEST_TYPE,
            wIndex=SET_WAVELENGTH,
            data_or_wLength=struct.pack("<f", position),
        )
        self._state['position'] = self._state['destination']
        
        delmot = abs(self.p_init - self._state["destination"])
        
        if self._state["turret"] == 'grating 1; 600 lines per mm':
            vitesse = 230
        elif self._state["turret"] == 'grating 2; 150 lines per mm':
            vitesse = 940
        elif self._state["turret"] == 'grating 3; 120 lines per mm':
            vitesse = 1150
        
        try:
            delay = 0.3 + round(delmot/vitesse,1)
            print(f'Changing position from {self.p_init} to {self._state["destination"]}: {delay} s')
            time.sleep(delay)
        except:
            delay = round(3)
            time.sleep(delay)
        
    async def update_state(self):
        while True:
            busy = self._dev.ctrl_transfer(
                B_REQUEST_IN, BM_REQUEST_TYPE, wIndex=IS_BUSY, data_or_wLength=4
            )
            self._busy = struct.unpack("<i", busy)[0]
            self._state["position"] = struct.unpack(
                "<f",
                self._dev.ctrl_transfer(
                    B_REQUEST_IN, BM_REQUEST_TYPE, wIndex=READ_WAVELENGTH, data_or_wLength=4
                ),
            )[0]
            self._state["position"] = self._state["position"] / (
                self._gratings[self._state["turret"]]["lines_per_mm"] / 1200.0
            )
            await asyncio.sleep(0.01)
            await self._busy_sig.wait()