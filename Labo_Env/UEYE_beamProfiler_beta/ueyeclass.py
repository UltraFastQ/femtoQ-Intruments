# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 11:50:13 2019

@author: Patrick
"""

from pyueye import ueye
import numpy as np


def gaussian(x, a, x0, sigma,b):
    
    f = a * np.exp( -2* (x-x0)**2 / sigma**2) +b
    
    return f

class UeyeCamera:

    def __init__(self, graphic=None, mainf=None):
        """
        Constructor.
        
        """
        
        self.camera = False
        self.graphic = graphic
        self.mainf = mainf
        self.detected_devices = {}

        self.hid = ueye.HIDS()
        self.sinfo = ueye.SENSORINFO()
        self.hwnd = ueye.HWND()
        self.width = None
        self.height = None
        self.psize = None
        self.bitspixel = ueye.INT(24)
        self.bytesppixel = int(self.bitspixel/8)
        self.ppcImgMem = ueye.c_mem_p()
        self.MemID = ueye.int()
        self.colorm = ueye.INT()
        self.pitch = ueye.INT()
        self.rect = ueye.IS_RECT()
        self.maxExp = ueye.double()
        self.minExp = ueye.double()
        self.Exp = ueye.double()
        self.nRet = None

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


    def return_devices(self):
        """ 
        Return list of connected camera.
        
        """
        
        varOut = []

        cam_num = ueye.INT()
        ueye.is_GetNumberOfCameras(cam_num)
        for i in range(cam_num.value):
            hid = ueye.HIDS(cam_num)
            s = ueye.is_InitCamera(self.hid, self.hwnd)
            r = ueye.is_GetSensorInfo(self.hid, self.sinfo)
            sname = self.sinfo.strSensorName.decode('UTF-8')
            self.detected_devices[sname] = i+1
            varOut.append(sname)
            ueye.is_ExitCamera(self.hid)
            
        return varOut

    def connect_device(self, name):
        """
        Connect to camera specified by name.
        
        """
        
        cam_num = self.detected_devices[name]
        cam_num = ueye.INT(cam_num)
        ueye.is_GetNumberOfCameras(cam_num)
        s = ueye.is_InitCamera(self.hid, self.hwnd)
        r = ueye.is_GetSensorInfo(self.hid, self.sinfo)
        self.configure_device()
        self.camera = True

    def disconnect_device(self):
        """
        Disconnect a previously connected camera.
        
        """

        ueye.is_FreeImageMem(self.hid, self.ppcImgMem, self.MemID)
        ueye.is_ExitCamera(self.hid)
        self.camera = False

    def configure_device(self):
        """
        Configure camera.
        
        """
        

        self.nRet = ueye.is_ResetToDefault(self.hid)
        if self.nRet != ueye.IS_SUCCESS:
            print('Reset ERROR')

        ueye.is_Exposure(self.hid, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MIN, self.minExp, 8)
        ueye.is_Exposure(self.hid, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MAX, self.maxExp, 8)

        self.nRet = ueye.is_SetDisplayMode(self.hid, ueye.IS_SET_DM_DIB)
        if self.nRet != ueye.IS_SUCCESS:
            print('Display Mode ERROR')
        ueye.is_Exposure(self.hid, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, self.minExp, 8 )
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
        self.pixelSizeMicron = self.sinfo.wPixelSize.value / 100

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
        #if self.nRet != ueye.IS_SUCCESS:
            #print('CaptureVideo ERROR')
        self.nRet = ueye.is_InquireImageMem(self.hid, self.ppcImgMem, self.MemID,
                                       self.width, self.height, self.bitspixel,
                                       self.pitch)
        if self.nRet != ueye.IS_SUCCESS:
            print('InquireImageMem ERROR')
        

    
    
    def acquire(self):
        """
        Acquire a single frame from the camera.
        
        """
        
        array = ueye.get_data(self.ppcImgMem, self.width, self.height, self.bitspixel, self.pitch, copy=False)
        frame = np.reshape(array,(self.height.value, self.width.value, self.bytesppixel))
        frame = frame[:,:,0]
        copiedFrame = np.copy(frame)
        
        return copiedFrame
    
    
    
    def set_exposure(self,exposure):
        """
        Set exposure parameter.
        """
        
        ueye.is_Exposure(self.hid, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, ueye.c_double(exposure), 8 )

























"""

def measure(self,x,y,plotWindowX,plotWindowY,imageWindow,crop,burntX):

        for i in range(2):
            array = ueye.get_data(self.ppcImgMem, self.width, self.height, self.bitspixel, self.pitch, copy=False)

            time.sleep(0.01)
            if i>0:
                frame = np.reshape(array,(self.height.value, self.width.value, self.bytesppixel))
                frame = frame[:,:,0]
                
                
                if burntX is not None:
                    nframe = frame[:,((x<burntX[0])|(x>burntX[1]))]
                    nx = x[((x<burntX[0])|(x>burntX[1]))]
                else:
                    nframe = frame
                    nx = x
                    
                maxPixel = np.max((nframe))
                
                nframe = nframe[:,((nx>crop[0])&(nx<crop[1]))]
                nframe = nframe[((y>crop[2])&(y<crop[3])),:]
                nx = nx[((nx>crop[0])&(nx<crop[1]))]
                ny = y[((y>crop[2])&(y<crop[3]))]
                
                frameX = np.mean(nframe,0)
                frameY = np.mean(nframe,1)
                
                meanX = np.trapz(nx*frameX,nx)/np.trapz(frameX,nx)
                meanY = np.trapz(ny*frameY,ny)/np.trapz(frameY,ny)
         
                
                stdX = np.sqrt(np.trapz((nx-meanX)**2*frameX,nx)/np.trapz(frameX,nx))
                stdY = np.sqrt(np.trapz((ny-meanY)**2*frameY,ny)/np.trapz(frameY,ny))
        
                maxX = np.max(frameX)
                maxY = np.max(frameY)
                minPixel = np.min((nframe))
                
                try:
                    paramX = opt.curve_fit(gaussian, nx,frameX, [maxX, meanX, stdX, minPixel])[0]
                    paramY = opt.curve_fit(gaussian, ny,frameY, [maxY, meanY, stdY, minPixel])[0]
                except:
                    paramX = [0,0,crop[1],0]
                    paramY = [0,0,crop[3],0]
                
                paramX[2] = abs(paramX[2])
                paramY[2] = abs(paramY[2])
                
                gaussX = gaussian(nx,paramX[0],paramX[1],paramX[2],paramX[3])
                gaussY = gaussian(ny,paramY[0],paramY[1],paramY[2],paramY[3])
                
                
                middleXStr = str( round( paramX[1]/1000, 1 ) )
                middleYStr = str( round( paramY[1]/1000, 1 ) )
                diamXStr = str( round( paramX[2], 1 ) )
                diamYStr = str( round( paramY[2], 1 ) )
                
    
                plotWindowX.plot(nx,frameX, pen=None, symbol='o', clear=True)
                plotWindowX.plot(nx,gaussX)
                plotWindowY.plot(frameY,ny, pen=None, symbol='o', clear=True)
                plotWindowY.plot(gaussY,ny)
                imageWindow.setImage(nframe.T)
                
                if maxPixel > 250:
                    plotWindowX.setLabel('bottom', 'SATURATION!!!! X: Centered: ' + middleXStr + ' mm, FW@e-2: ' + diamXStr + ' um')
                    plotWindowY.setLabel('bottom', 'SATURATION!!!! Y: Centered: ' + middleYStr + ' mm, FW@e-2: ' + diamYStr + ' um')
                else:
                    plotWindowX.setLabel('bottom', 'X: Centered: ' + middleXStr + ' mm, FW@e-2: ' + diamXStr + ' um')
                    plotWindowY.setLabel('bottom', 'Y: Centered: ' + middleYStr + ' mm, FW@e-2: ' + diamYStr + ' um')
                pg.QtGui.QApplication.processEvents()
                time.sleep(0.01)
                
        return paramX[1],paramY[1]








"""