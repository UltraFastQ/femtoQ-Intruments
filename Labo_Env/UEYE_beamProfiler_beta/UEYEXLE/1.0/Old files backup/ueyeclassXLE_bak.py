# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 11:50:13 2019

@author: Patrick
"""
from ids_peak import ids_peak
from ids_peak_ipl import ids_peak_ipl
from ids_peak import ids_peak_ipl_extension

VERSION = "1.0.1"
FPS_LIMIT = 30

import numpy as np


def gaussian(x, a, x0, sigma,b):
    
    f = a * np.exp( -2* (x-x0)**2 / sigma**2) +b
    
    return f

class UeyeCamera:

    def __init__(self):
        """
        Constructor.
        
        """
        
        self.camera = False
        self.detected_devices = {}
        self.width = None
        self.height = None
        self.psize = None
        self.nRet = None
        
        self.__device = None
        self.__nodemap_remote_device = None
        self.__datastream = None

        self.__display = None
        self.__frame_counter = 0
        self.__error_counter = 0
        self.__acquisition_running = False

        self.__label_infos = None
        self.__label_version = None
        self.__label_aboutqt = None
        
        



    def return_devices(self):
        """ 
        Return list of connected cameras.
        
        """
         # initialize library
        ids_peak.Library.Initialize()
    
        # Create instance of the device manager
        self.__device_manager = ids_peak.DeviceManager.Instance()

        # Update the device manager
        self.__device_manager.Update()

        # Return if no device was found
        if self.__device_manager.Devices().empty():
            print("Error", "No device found!")
            return False

            
        return self.__device_manager.Devices()



    def connect_device(self, devices):
        """
        Connect to camera specified by name.
        
        """
        # Open the first openable device in the managers device list
        for device in devices:
            if device.IsOpenable():
                self.__device = device.OpenDevice(ids_peak.DeviceAccessType_Control)
                break

        # Return if no device could be opened
        if self.__device is None:
            print("Error", "Device could not be opened!")
            return False
        self.camera = True
        

        return True



    def disconnect_device(self):
        """
        Disconnect a previously connected camera.
        
        """
        """
        Stop acquisition if still running and close datastream and nodemap of the device
        """
        # Check that a device is opened and that the acquisition is running. If not, return.
        if self.__device is None:
            return

        # Otherwise try to stop acquisition
        if self.__acquisition_running:
            try:
                # Stop acquisition timer and camera acquisition
                remote_nodemap = self.__device.RemoteDevice().NodeMaps()[0]
                remote_nodemap.FindNode("AcquisitionStop").Execute()
    
                self.__acquisition_running = False
            except Exception as e:
                print("Exception", str(e))
            # Stop and flush datastream
            self.__datastream.KillWait()
            self.__datastream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)
            self.__datastream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)

        # Unlock parameters after acquisition stop
        if self.__nodemap_remote_device is not None:
            try:
                self.__nodemap_remote_device.FindNode("TLParamsLocked").SetValue(0)
            except Exception as e:
                print("Exception", str(e))
        # If a datastream has been opened, try to revoke its image buffers
        if self.__datastream is not None:
            try:
                for buffer in self.__datastream.AnnouncedBuffers():
                    self.__datastream.RevokeBuffer(buffer)
            except Exception as e:
                print("Exception", str(e))
        return



    def configure_device(self):
        """
        Configure camera.
        
        """
        # Open standard data stream
        datastreams = self.__device.DataStreams()
        if datastreams.empty():
           print("Error", "Device has no DataStream!")
           self.__device = None
           return False

        self.__datastream = datastreams[0].OpenDataStream()

        # Get nodemap of the remote device for all accesses to the genicam nodemap tree
        self.__nodemap_remote_device = self.__device.RemoteDevice().NodeMaps()[0]
        self.EZnodemap = self.__device.RemoteDevice().NodeMaps()[0]

        # To prepare for untriggered continuous image acquisition, load the default user set if available and
        # wait until execution is finished
        try:
            self.__nodemap_remote_device.FindNode("UserSetSelector").SetCurrentEntry("Default")
            self.__nodemap_remote_device.FindNode("UserSetLoad").Execute()
            self.__nodemap_remote_device.FindNode("UserSetLoad").WaitUntilDone()
        except ids_peak.Exception:
            # Userset is not available
            pass

        self.EZnodemap.FindNode('PixelFormat').SetCurrentEntry('Mono12g24IDS')
        self.EZnodemap.FindNode('BinningHorizontal').SetValue(1)
        self.EZnodemap.FindNode('ExposureTime').SetValue(50)
        self.EZnodemap.FindNode('AcquisitionFrameRate').SetValue(10)
        
        
        # Get the payload size for correct buffer allocation
        payload_size = self.__nodemap_remote_device.FindNode("PayloadSize").Value()

        # Get minimum number of buffers that must be announced
        buffer_count_max = self.__datastream.NumBuffersAnnouncedMinRequired()

        # Allocate and announce image buffers and queue them
        for i in range(buffer_count_max):
            buffer = self.__datastream.AllocAndAnnounceBuffer(payload_size)
            self.__datastream.QueueBuffer(buffer)
            
        return

    def get_pixel_format_list(self):
        allEntries = self.EZnodemap.FindNode("PixelFormat").Entries()
        availableEntries = []
        for entry in allEntries:
          if (entry.AccessStatus() != ids_peak.NodeAccessStatus_NotAvailable
                  and entry.AccessStatus() != ids_peak.NodeAccessStatus_NotImplemented):
              availableEntries.append(entry.SymbolicValue())
        return availableEntries
    
    def acquire(self):
        """
        Acquire a single frame from the camera.
        
        """
        
        
        # Check that a device is opened and that the acquisition is NOT running. If not, return.
        if self.__device is None:
            return False

        # Get the maximum framerate possible, limit it to the configured FPS_LIMIT. If the limit can't be reached, set
        # acquisition interval to the maximum possible framerate
        
        if not self.__acquisition_running:
            try:
                max_fps = self.__nodemap_remote_device.FindNode("AcquisitionFrameRate").Maximum()
                target_fps = min(max_fps, FPS_LIMIT)
                self.__nodemap_remote_device.FindNode("AcquisitionFrameRate").SetValue(target_fps)
            except ids_peak.Exception:
                # AcquisitionFrameRate is not available. Unable to limit fps. Print warning and continue on.
                print( "Warning",
                                    "Unable to limit fps, since the AcquisitionFrameRate Node is"
                                    " not supported by the connected camera. Program will continue without limit.")
    
            try:
                # Lock critical features to prevent them from changing during acquisition
                self.__nodemap_remote_device.FindNode("TLParamsLocked").SetValue(1)
    
                # Start acquisition on camera
                self.__datastream.StartAcquisition()
                self.__nodemap_remote_device.FindNode("AcquisitionStart").Execute()
                self.__nodemap_remote_device.FindNode("AcquisitionStart").WaitUntilDone()
            except Exception as e:
                print("Exception: " + str(e))
                return False
            self.__acquisition_running = True
            
        try:
            # Get buffer from device's datastream
            buffer = self.__datastream.WaitForFinishedBuffer(5000)

                        # Create IDS peak IPL image for debayering and convert it to RGBa8 format
            #ipl_image = ids_peak_ipl_extension.BufferToImage(buffer)
            ipl_image = ids_peak_ipl.Image_CreateFromSizeAndBuffer(
                  buffer.PixelFormat(),
                  buffer.BasePtr(),
                  buffer.Size(),
                  buffer.Width(),
                  buffer.Height()
               )
            
            converted_ipl_image_12 = ipl_image.ConvertTo(ids_peak_ipl.PixelFormatName_Mono12)
            converted_ipl_image_8 = ipl_image.ConvertTo(ids_peak_ipl.PixelFormatName_Mono8)
            converted_ipl_image_10 = ipl_image.ConvertTo(ids_peak_ipl.PixelFormatName_Mono10)

            # Queue buffer so that it can be used again
            self.__datastream.QueueBuffer(buffer)

            # Get raw image data from converted image and construct a QImage from it
            #image_np_array = converted_ipl_image.get_numpy_1D()
# =============================================================================
#             image = QImage(image_np_array,
#                            converted_ipl_image.Width(), converted_ipl_image.Height(),
#                            QImage.Format_RGB32)
# 
#             # Make an extra copy of the QImage to make sure that memory is copied and can't get overwritten later on
#             image_cpy = image.copy()
# 
#             # Emit signal that the image is ready to be displayed
#             self.__display.on_image_received(image_cpy)
#             self.__display.update()
# 
#             # Increase frame counter
#             self.__frame_counter += 1
#         except ids_peak.Exception as e:
#             self.__error_counter += 1
#             print("Exception: " + str(e))
# =============================================================================

            array_8to8 = converted_ipl_image_8.get_numpy_2D()
            array_10to16 = converted_ipl_image_10.get_numpy_2D_16()
            array_12to16 = converted_ipl_image_12.get_numpy_2D_16()
            #frame = np.reshape(array,(converted_ipl_image.Height(),converted_ipl_image.Width()))
            #frame = frame[:,:,0]
            #copiedFrame = np.copy(frame)
        except ids_peak.Exception as e:
            self.__error_counter += 1
            print("Exception: " + str(e))
        
        return array_8to8.copy(),array_10to16.copy(),array_12to16.copy()
    
    
    
    def set_exposure(self,exposure):
        """
        Set exposure parameter.
        """
        return

























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