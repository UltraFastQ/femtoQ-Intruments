import asyncio
import struct
import time

import usb.core  # type: ignore

from _horiba_mono import (
    HoribaMono,
    IHR320_ID_PRODUCT,
    B_REQUEST_IN,
    B_REQUEST_OUT,
    BM_REQUEST_TYPE,
    READ_SLITWIDTH,
    SET_SLITWIDTH,
    READ_MIRROR,
    SET_MIRROR,
    IS_BUSY,
    READ_WAVELENGTH,
)

__all__ = ["HoribaIHR320"]


class HoribaIHR320(HoribaMono):
    _kind = "horiba-ihr320"
    _ID_PRODUCT = IHR320_ID_PRODUCT

    """
    async def _reset_position(self):
        await super()._reset_position()
        
        for i in range(2):
            self._set_mirror(i, self._state["mirrors_dest"][i])
        for i in range(4):
            self._set_slit(i, self._state["slits_dest"][i])
            print(i)
    """ 

    def _get_slit(self, index: int):
        # this assumes 7 mm slits, may be different for 2 mm slits
        const = 7 / 1000
        data = self._dev.ctrl_transfer(
            B_REQUEST_IN, BM_REQUEST_TYPE, wIndex=READ_SLITWIDTH, data_or_wLength=4, wValue=index
        )
        return const * struct.unpack("<i", data)[0]

    def _set_slit(self, index: int, width: float):
        """Set slit with index to width (in mm)"""
        self._busy = True
        
        
        message1 = 'changing slit'
        message2 = 'slit changed'
        delay = 2.5

        self._state["slits_dest"][index] = width
        
        const = 7 / 1000
        
        self._dev.ctrl_transfer(
            B_REQUEST_OUT,
            BM_REQUEST_TYPE,
            wIndex=SET_SLITWIDTH,
            data_or_wLength=struct.pack("<i", round(width / const)),
            wValue=index,
        )
        
        print(f'{message1}: {delay} s')
        time.sleep(delay)
        print(message2)
        
        self._state["slits"][index] = self._get_slit(index)

    def get_front_entrance_slit(self) -> float:
        return self._state["slits"][0]

    def get_side_entrance_slit(self) -> float:
        return self._state["slits"][1]

    def get_front_exit_slit(self) -> float:
        return self._state["slits"][2]

    def get_side_exit_slit(self) -> float:
        return self._state["slits"][3]

    def set_front_entrance_slit(self, width):
        return self._set_slit(0, width)

    def set_side_entrance_slit(self, width):
        return self._set_slit(1, width)

    def set_front_exit_slit(self, width):
        return self._set_slit(2, width)

    def set_side_exit_slit(self, width):
        return self._set_slit(3, width)

    def _get_mirror(self, index: int):
        # this assumes 2 mm slits, may be different for 7 mm slits
        data = self._dev.ctrl_transfer(
            B_REQUEST_IN, BM_REQUEST_TYPE, wIndex=READ_MIRROR, data_or_wLength=4, wValue=index
        )
        return "side" if bool(struct.unpack("<i", data)[0]) else "front"

    def _set_mirror(self, index: int, side: str):
        """Set mirror with index to front or side"""
        self._busy = True
        self._state["mirrors_dest"][index] = side
        self._dev.ctrl_transfer(
            B_REQUEST_OUT,
            BM_REQUEST_TYPE,
            wIndex=SET_MIRROR,
            data_or_wLength=struct.pack("<i", side == "side"),
            wValue=index,
        )

    def get_entrance_mirror(self):
        return self._state["mirrors"][0]

    def get_exit_mirror(self):
        return self._state["mirrors"][1]

    def set_entrance_mirror(self, side: str):
        self._busy = True
        self._set_mirror(0, side)

    def set_exit_mirror(self, side: str):
        self._busy = True
        self._set_mirror(1, side)

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
            for i in range(4):
                self._state["slits"][i] = self._get_slit(i)
            for i in range(2):
                self._state["mirrors"][i] = self._get_mirror(i)
            await asyncio.sleep(0.01)
            await self._busy_sig.wait()

"""
name='ihr32'
config={'port':2,
        'out_of_limits':'closest',
        'gratings':{'grating 1; 600 lines per mm':{'lines_per_mm':600,'index':0},
                    'grating 2; 150 lines per mm':{'lines_per_mm':150,'index':1},
                    'grating 3; 120 lines per mm':{'lines_per_mm':120,'index':2}
                    },
        'limits':[0,15800]

        }

config_path = ''
d = HoribaIHR320(name,config,config_path)
"""

#d.set_position(100)
#d.set_turret(d.get_turret_options()[0])
#d.set_front_entrance_slit(1)
#d.set_front_exit_slit(1)
#d.set_position(699)
#631.3 grating 1, sw: 0.02 et 0.01 fkn précis
#622.4 grating 2, sw: 0.04 et 0.1
#627.5 grating 3, sw: 0.04 et 0.1

# slit width
"""
while True:
    sw = input('sw: ')
    if sw == 'None':
        break
    else:
        sw = float(sw)
        d.set_front_entrance_slit(sw)
        d.set_front_exit_slit(sw)
"""
"""
# position
while True:
    pos = input('pos: ')
    if pos == 'None':
        break
    else:
        pos = float(pos)
        d.set_position(pos)
"""
"""
for i in range(1):
    
    print('debut for')
    d.set_position(10)
    time.sleep(3)
    pos = d.get_position()
    

    d.set_turret(d.get_turret_options()[i])
    d.set_position(10)
    
    while pos < (i+1)*1100:
    
        time.sleep(8)
        t2=time.time()
        d.set_relative(20)
        pos = d.get_position()
        print(pos,d.get_exit_mirror())
    print('position > 1100')
    print(d._state)
    time.sleep(5)
"""
"""
print('here')
d.set_position(100)
time.sleep(5)
d.set_turret(d.get_turret_options()[0])
d.set_front_entrance_slit(5)
d.set_front_exit_slit(5)
d.set_side_exit_slit(5)
print(d._state) 
"""