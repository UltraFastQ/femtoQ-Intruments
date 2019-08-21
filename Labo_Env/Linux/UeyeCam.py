try:
    from pyueye import ueye
    import cv2
except:
    pass
from tkinter import messagebox
import numpy as np




class UeyeCamera:

    def __init__(self, graphic=None, mainf=None):
        self.camera = False
        self.graphic = graphic
        self.mainf = mainf
        self.detected_devices = {}
        try:
            self.hid = ueye.HIDS()
            self.sinfo = ueye.SENSORINFO()
            self.hwnd = ueye.HWND()
            self.width = ueye.INT()
            self.height = ueye.INT()
            self.psize = None
            self.bitspixel = ueye.INT(24)
            self.ppcImgMem = ueye.c_mem_p()
            self.pid = ueye.INT()
            self.MemID = ueye.INT()
            self.colorm = ueye.INT()
            self.pitch = ueye.INT()
            self.rect = ueye.IS_RECT()
        except:
            return

    def return_devices(self, variable):

        cam_num = ueye.INT()
        ueye.is_GetNumberOfCameras(cam_num)
        for i in range(cam_num.value):
            hid = ueye.HIDS(cam_num)
            s = ueye.is_InitCamera(self.hid, self.hwnd)
            r = ueye.is_GetSensorInfo(self.hid, self.sinfo)
            sname = self.sinfo.strSensorName.decode('UTF-8')
            self.detected_devices[sname] = i+1
            variable.insert('end', sname)
            ueye.is_ExitCamera(self.hid)

    def connect_device(self, variable):
        if not variable.curselection():
            messagebox.showinfo(title='Error', message='No'+
                                'device selected!')
            return
        index = variable.curselection()[0]
        name = variable.get(index)
        cam_num = self.detected_devices[name]
        cam_num = ueye.INT(cam_num)
        ueye.is_GetNumberOfCameras(cam_num)
        s = ueye.is_InitCamera(self.hid, self.hwnd)
        r = ueye.is_GetSensorInfo(self.hid, self.sinfo)
        self.configure_device()
        self.configure_graph()
        self.camera = True


    def disconnect_device(self, variable=None):

        ueye.is_FreeImageMem(self.hid, self.ppcImgMem, self.pid)
        ueye.is_ExitCamera(self.hid)
        self.camera = False

        if variable:
            variable.delete(0,'end')
            self.return_devices(variable)

    def configure_device(self):
        self.width = self.sinfo.nMaxWidth
        self.height = self.sinfo.nMaxHeight
        self.psize = self.sinfo.wPixelSize
        nRet = ueye.is_ResetToDefault(self.hid)
        if nRet != ueye.IS_SUCCESS:
            print('Reset ERROR')
        nRet = ueye.is_SetDisplayMode(self.hid, ueye.IS_SET_DM_DIB)
        if nRet != ueye.IS_SUCCESS:
            print('Display Mode ERROR')
        nRet = ueye.is_AOI(self.hid, ueye.IS_AOI_IMAGE_GET_AOI, self.rect,
                           ueye.sizeof(self.rect))
        self.width = self.rect.s32Width
        self.height = self.rect.s32Height
        print(self.width.value, self.height.value)
        if nRet != ueye.IS_SUCCESS:
            print('AOI ERROR')
        nRet = ueye.is_AllocImageMem(self.hid, self.width, self.height,
                                     self.bitspixel, self.ppcImgMem,
                                     self.pid)
        if nRet != ueye.IS_SUCCESS:
            print('AllocImageMem ERROR')
        nRet = ueye.is_SetImageMem(self.hid, self.ppcImgMem, self.pid)
        if nRet != ueye.IS_SUCCESS:
            print('SetImageMem ERROR')
        nRet = ueye.is_SetColorMode(self.hid, self.colorm)
        if nRet != ueye.IS_SUCCESS:
            print('SetColorMode ERROR')
        nRet = ueye.is_CaptureVideo(self.hid, ueye.IS_DONT_WAIT)
        if nRet != ueye.IS_SUCCESS:
            print('CaptureVideo ERROR')
        nRet = ueye.is_InquireImageMem(self.hid, self.ppcImgMem, self.pid,
                               self.width, self.height, self.bitspixel,
                               self.pitch)
        if nRet != ueye.IS_SUCCESS:
            print('InquireImageMem ERROR')
        ueye.is_Exposure(self.hid, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE,
                         ueye.double(100), 8)
        array = ueye.get_data(self.ppcImgMem, self.width.value,
                              self.height.value, self.bitspixel, self.pitch,
                              copy=False)
        array = np.reshape(array, (self.height.value, self.width.value,
                                   int(self.bitspixel/8)))
        a = np.all(array==0)
        print(a)
        print(array[int(len(array)/2), int(len(array)/2)-10:int(len(array)/2)+10])
        frame = cv2.resize(array, (int(self.height.value*0.2), int(self.width*0.2)), (0,0))
        print(frame)
        self.disconnect_device()

    def configure_graph(self):
        pass
