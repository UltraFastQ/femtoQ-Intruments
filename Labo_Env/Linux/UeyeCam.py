try:
    from pyueye import ueye
    import cv2
except:
    pass
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
plt.ion()
import time


class UeyeCamera:

    def __init__(self, graphic=None, mainf=None):
        self.camera = False
        self.graphic = graphic
        self.mainf = mainf
        self.detected_devices = {}
        self.nRet = None
        try:
            self.hid = ueye.HIDS()
            self.sinfo = ueye.SENSORINFO()
            self.hwnd = ueye.HWND()
            self.width = ueye.INT()
            self.height = ueye.INT()
            self.psize = None
            self.bitspixel = ueye.INT(24)
            self.bytesppixel = int(self.bitspixel/8)
            self.ppcImgMem = ueye.c_mem_p()
            self.pid = ueye.INT()
            self.MemID = ueye.INT()
            self.colorm = ueye.INT()
            self.pitch = ueye.INT()
            self.rect = ueye.IS_RECT()
            self.maxExp = ueye.double()
            self.minExp = ueye.double()
            self.Exp = ueye.double()
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

        ueye.is_FreeImageMem(self.hid, self.ppcImgMem, self.MemID)
        ueye.is_ExitCamera(self.hid)
        self.camera = False

        if variable:
            variable.delete(0,'end')
            self.return_devices(variable)

    def configure_device(self):

        self.nRet = ueye.is_ResetToDefault(self.hid)
        if self.nRet != ueye.IS_SUCCESS:
            print('Reset ERROR')

        ueye.is_Exposure(self.hid, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MIN, self.minExp, 8)
        ueye.is_Exposure(self.hid, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MAX, self.maxExp, 8)

        self.nRet = ueye.is_SetDisplayMode(self.hid, ueye.IS_SET_DM_DIB)
        if self.nRet != ueye.IS_SUCCESS:
            print('Display Mode ERROR')
        ueye.is_Exposure(self.hid, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, ueye.c_double(1), 8 )
        ueye.is_Exposure(self.hid, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE, self.Exp, 8 )
        # Set the right color mode
        if int.from_bytes(self.sinfo.nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_BAYER:
            # setup the color depth to the current windows setting
            ueye.is_GetColorDepth(self.hid, self.bitspixel, self.colorm)
            self.bytesppixel = int(self.bitspixel / 8)

        elif int.from_bytes(self.sinfo.nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_CBYCRY:
            # for color camera models use RGB32 mode
            self.colorm = ueye.IS_CM_BGRA8_PACKED
            self.bitspixel = ueye.INT(32)
            self.bytesppixel = int(self.bitspixel / 8)

        elif int.from_bytes(self.sinfo.nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_MONOCHROME:
            # for color camera models use RGB32 mode
            self.colorm = ueye.IS_CM_MONO8
            self.bitspixel = ueye.INT(8)
            self.bytesppixel = int(self.bitspixel / 8)
        else:
            # for monochrome camera models use Y8 mode
            self.colorm = ueye.IS_CM_MONO8
            self.bitspixel = ueye.INT(8)
            self.bytesppixel = int(self.bitspixel / 8)

        self.nRet = ueye.is_AOI(self.hid, ueye.IS_AOI_IMAGE_GET_AOI, self.rect,
                           ueye.sizeof(self.rect))
        self.width = self.rect.s32Width
        self.height = self.rect.s32Height

        if self.nRet != ueye.IS_SUCCESS:
            print('AOI ERROR')
        self.nRet = ueye.is_AllocImageMem(self.hid, self.width, self.height,
                                     self.bitspixel, self.ppcImgMem,
                                     self.MemID)
        if self.nRet != ueye.IS_SUCCESS:
            print('AllocImageMem ERROR')
        else:
            self.nRet = ueye.is_SetImageMem(self.hid, self.ppcImgMem, self.MemID)
            if self.nRet != ueye.IS_SUCCESS:
                print('SetImageMem ERROR')
            else:
                self.nRet = ueye.is_SetColorMode(self.hid, self.colorm)

        self.nRet = ueye.is_CaptureVideo(self.hid, ueye.IS_DONT_WAIT)
        if self.nRet != ueye.IS_SUCCESS:
            print('CaptureVideo ERROR')
        self.nRet = ueye.is_InquireImageMem(self.hid, self.ppcImgMem, self.MemID,
                                       self.width, self.height, self.bitspixel,
                                       self.pitch)
        if self.nRet != ueye.IS_SUCCESS:
            print('InquireImageMem ERROR')
        for i in range(10):
            self.measure()
        self.disconnect_device()

    def measure(self):
        print('Creating figure')
        fig = plt.figure(figsize=(6,6))
        ax = fig.add_subplot(111)
        ax.set_title('colorMap')
        ax.set_aspect('equal')
        plt.imshow(np.zeros((10,10)), cmap='viridis')
        plt.show()
        if (self.nRet != ueye.IS_SUCCESS):
            return
        # Continuous image display
        for i in range(2):
            print('Starting loop')
            # In order to display the image in an OpenCV window we need to...
            # ...extract the data of our image memory
            array = ueye.get_data(self.ppcImgMem, self.width, self.height, self.bitspixel, self.pitch, copy=False)
            # bytes_per_pixel = int(nBitsPerPixel / 8)

            # ...reshape it in an numpy array...
            frame = np.reshape(array,(self.height.value, self.width.value, self.bytesppixel))
            plt.imshow(frame[:,:,0], cmap='viridis')
            # ...resize the image by a half
            #frame = cv2.resize(frame,(0,0),fx=0.5, fy=0.5)

            #-----------------------------------------------------------------------------------------------------------
                #Include image data processing here

            #------------------------------------------------------------------------------------------------------------

            #...and finally display it
            #cv2.imshow("SimpleLive_Python_uEye_OpenCV", frame)

            # Press q if you want to end the loop
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break
            plt.show()
            time.sleep(1)
#        array = ueye.get_data(self.ppcImgMem, self.width,
#                              self.height, self.bitspixel, self.pitch,
#                              copy=False)
#        print(array)
#        array = np.reshape(array, (self.height.value, self.width.value,
#                                   self.bytesppixel))
#
#        frame = cv2.resize(array, (0,0), fx=0.5, fy=0.5)
#        self.disconnect_device()
#        cv2.imshow('simple live', frame)

    def configure_graph(self):
        pass
