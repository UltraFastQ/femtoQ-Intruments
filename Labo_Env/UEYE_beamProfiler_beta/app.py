# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 11:44:18 2019

@author: Patrick
"""

import sys
from PyQt5 import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import ueyeclass as ueye
import scipy.optimize as opt
import os
import datetime





class ueye_beam_profiler(QtGui.QWidget):
    
    
    def __init__(self, camName, camHandle):
        """ 
        Constructor function. Creates a gui window to display and control a
        ueye camera.
        
        Inputs:
            - camName: Name of connected camera.
            - camHandle: Handle object to control the connected camera
        """
       
        
        """ Acquire camera parameters """
        self.camName = camName
        self.camHandle = camHandle
        self.camExposure = self.camHandle.Exp.value
        self.camExposureMin = self.camHandle.minExp.value
        self.camExposureMax = self.camHandle.maxExp.value
        self.pixelSize = camHandle.pixelSizeMicron
        self.numberVerticalPixels = self.camHandle.height.value
        self.numberHorizontalPixels = self.camHandle.width.value
        self.horizontalLength = self.numberHorizontalPixels*self.pixelSize
        self.verticalLength = self.numberVerticalPixels*self.pixelSize
        self.today = str(datetime.date.today())
        self.saveFolder = 'Data\\' + self.today
        self.ensure_data_folder_exists()
        
        """ Settings """
        self.x = np.linspace(0.5,self.numberHorizontalPixels-0.5,self.numberHorizontalPixels)*self.pixelSize
        self.y = np.linspace(0.5,self.numberVerticalPixels-0.5,self.numberVerticalPixels)*self.pixelSize
        self.X, self.Y = np.meshgrid(self.x,self.y)                                                                                       
        self.xHighRes = np.linspace(0.5,self.numberHorizontalPixels-0.5,self.numberHorizontalPixels*4)*self.pixelSize
        self.yHighRes = np.linspace(0.5,self.numberVerticalPixels-0.5,self.numberVerticalPixels*4)*self.pixelSize
        self.yRange = [0, 255]
        self.plotGaussianFits = False
        self.displayCameraImage = True
        self.beamCenterHorizontal = self.numberHorizontalPixels*self.pixelSize / 2
        self.beamCenterVertical = self.numberVerticalPixels*self.pixelSize / 2
        self.zoomValue = 1
        self.applyZoom = False
        self.maxCounts = 0
        self.exposureSliderNumberSteps = 50
        self.checkBurntRows = False
        self.checkBurntColumns = False
        self.countsThresholdBurntPixels = 50
        self.updateZoomCenter = False
        
        print('Model: ' + self.camName)
        print('Pixel resolution: ' + str(self.pixelSize) + ' um')
        print('Exposure range: [' + str(round(self.camExposureMin,2)) + ' , ' + str(round(self.camExposureMax,2)) + '] ms')
 
        
        
        """ Initialize gui """
        super(ueye_beam_profiler, self).__init__()
        self.init_ui()
        self.qt_connections()
        
        """ Create figures """
        # Camera display
        view = self.canvas.addViewBox(0,1,enableMouse = False)
        self.plotImage = pg.ImageItem(None, border="w")
        view.addItem(self.plotImage)
        
        # X projection
        self.plotImageX = self.canvas.addPlot(1,1,enableMouse = False)
        self.plotImageX.setYRange(self.yRange[0],self.yRange[1])

        # Y projection
        self.plotImageY = self.canvas.addPlot(0,0,enableMouse = False)
        self.plotImageY.setXRange(self.yRange[0],self.yRange[1])
        
        # Text display
        textview = self.canvas.addViewBox(1,0,enableMouse = False)
        textview.setRange(QtCore.QRectF(0, -100, 100, 100))
        self.set_text('initialize')
        textview.addItem(self.textBox)
        
        qGraphicsGridLayout = self.canvas.ci.layout
        qGraphicsGridLayout.setColumnMinimumWidth(0, 50)
        qGraphicsGridLayout.setColumnMinimumWidth(1, 300)
        qGraphicsGridLayout.setColumnStretchFactor(0, 1)
        qGraphicsGridLayout.setColumnStretchFactor(1, 2)
        qGraphicsGridLayout.setRowMinimumHeight(1, 50)
        qGraphicsGridLayout.setRowMinimumHeight(0, 300)
        qGraphicsGridLayout.setRowStretchFactor(1, 1)
        qGraphicsGridLayout.setRowStretchFactor(0, 2)
        #qGraphicsGridLayout.setRowStretchFactor(0, 1)
        #qGraphicsGridLayout.setRowStretchFactor(1, 0.95)
        
        """ Main loop """ 
        self.update_plot()
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()


    def init_ui(self):
        
        """
        Function that defines the actual layout of the gui window.
        """
        
        """ Create window """
        self.mainbox = QtGui.QWidget()
        self.setWindowTitle('Ueye laser beam profiler')
        
        """ Add figures as main display """
        vbox = QtGui.QVBoxLayout(self.mainbox)
        hbox_0 = QtGui.QHBoxLayout()
        hbox_1 = QtGui.QHBoxLayout()
        self.setLayout(vbox)
        self.canvas = pg.GraphicsLayoutWidget()
        vbox.addWidget(self.canvas)

        """ Add controls under main display """
        
        # Exposure time
        self.label = QtGui.QLabel("Exposure time")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.exposureSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.exposureSlider.setMinimum(0)
        self.exposureSlider.setMaximum( self.exposureSliderNumberSteps-1)
        self.exposureSlider.setValue(0)
        self.exposureSlider.setSingleStep(0)
        
        # Burnt pixel detection
        self.burntcolumnscheckbox = QtGui.QCheckBox("Detect and ignore burnt columns (experimental)")
        self.burntrowscheckbox = QtGui.QCheckBox("Detect and ignore burnt rows  (experimental)")
        
        # 
        self.fitcheckbox = QtGui.QCheckBox("Toggle gaussian fits")
        self.imagecheckbox = QtGui.QCheckBox("Toggle camera display")
        self.zoomLabel = QtGui.QLabel("Zoom value: ")
        self.zoomLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.zoomValuetextbox = QtGui.QLineEdit(str(self.zoomValue))
        self.zoomValuecheckbox = QtGui.QCheckBox("Toggle zoom")
        self.zoomCentercheckbox = QtGui.QCheckBox("Toggle zoom position update")
        
        
        self.saveDataButton = QtGui.QPushButton("Save image data")
        
        # Add widgets to gui. Widgets in vbox are stacked vertically, while
        # those in hbox_1 are stacked horizontally
        hbox_0.addWidget(self.label)
        hbox_0.addWidget(self.exposureSlider)
        
        hbox_1.addWidget(self.fitcheckbox)
        hbox_1.addWidget(self.imagecheckbox)
        hbox_1.addWidget(self.zoomLabel)
        hbox_1.addWidget(self.zoomValuetextbox)
        hbox_1.addWidget(self.zoomValuecheckbox)
        hbox_1.addWidget(self.zoomCentercheckbox)
        hbox_1.addWidget(self.burntcolumnscheckbox)
        hbox_1.addWidget(self.burntrowscheckbox)
        hbox_1.addWidget(self.saveDataButton)
        
        
        vbox.addLayout(hbox_0)
        vbox.addLayout(hbox_1)
        
        
        # Window size and display
        self.setGeometry(50, 50, 1000, 600)
        self.show()

    def qt_connections(self):
        """ 
        Connect widgets to their callback function.
        
        """
        
        self.exposureSlider.valueChanged.connect(self.on_exposure_slider_adjustment)
        self.burntcolumnscheckbox.stateChanged.connect(self.on_burnt_columns_checkbox_clicked)
        self.burntrowscheckbox.stateChanged.connect(self.on_burnt_rows_checkbox_clicked)
        self.fitcheckbox.stateChanged.connect(self.on_gaussian_fits_checkbox_clicked)
        self.imagecheckbox.stateChanged.connect(self.on_image_display_checkbox_clicked)
        self.zoomValuetextbox.returnPressed.connect(self.on_zoom_value_edited)
        self.zoomValuecheckbox.stateChanged.connect(self.on_zoom_checkbox_clicked)
        self.zoomCentercheckbox.stateChanged.connect(self.on_zoom_centering_checkbox_cliked)
        
        self.saveDataButton.clicked.connect(self.on_save_button_pressed)

    def update_plot(self):
        """
        Acquire, process and display data.
        
        """
        self.dataImage = self.camHandle.acquire()
        
        
        if self.checkBurntRows:
            visibleUnburntRows = self.unburntRows
        if self.checkBurntColumns:
            visibleUnburntColumns = self.unburntColumns
        
        if self.checkBurntRows:
            self.dataImage[np.logical_not(visibleUnburntRows),:] = 0
            
        if self.checkBurntColumns:
            self.dataImage[:,np.logical_not(visibleUnburntColumns)] = 0
          
        
        x = self.x
        y = self.y
        
        
        if self.updateZoomCenter:
            
            indices = np.unravel_index(np.argmax(self.dataImage, axis=None), self.dataImage.shape)
            self.beamCenterHorizontal = x[indices[1]]
            self.beamCenterVertical = y[indices[0]]
            #print('index: '+ str(indices[0]) + ', position: ' + str(y[indices[0]]))
        
        self.maxCounts = np.max(self.dataImage)    
        
        if self.applyZoom:
            displayRadX = self.numberHorizontalPixels * self.pixelSize/2  / self.zoomValue
            displayRadY = self.numberVerticalPixels * self.pixelSize/2  / self.zoomValue
            
            self.dataImage = self.dataImage[ : , np.abs(x-self.beamCenterHorizontal) < displayRadX]
            self.dataImage = self.dataImage[np.abs(y-self.beamCenterVertical) < displayRadY, :]
        
        
        """ Take a cut at the beam's center. Not working yet. """
# =============================================================================
#         dataX = self.dataImage[np.argmin(np.abs(self.y - self.beamCenterVertical)),:]
#         dataY = self.dataImage[:,np.argmin(np.abs(self.x - self.beamCenterHorizontal))]
# =============================================================================
        
        """ Take averaged projections along x and y axis. """
        maxPixel = np.max(self.dataImage)
        
        dataX = np.mean(self.dataImage,0)
        minX = np.min(dataX)
        dataX = (dataX - minX)/np.max(dataX - minX) * maxPixel
        
        dataY = np.mean(self.dataImage,1)
        minY = np.min(dataY)
        dataY = (dataY - minY)/np.max(dataY - minY) * maxPixel
        
        xHighRes = self.xHighRes
        yHighRes = self.yHighRes
        
        
        
        if self.applyZoom:
            
            if self.checkBurntRows:
                visibleUnburntRows = self.unburntRows[ np.abs(y-self.beamCenterVertical) < displayRadY]
            if self.checkBurntColumns:
                visibleUnburntColumns = self.unburntColumns[ np.abs(x-self.beamCenterHorizontal) < displayRadX]
            
            x = x[ np.abs(x-self.beamCenterHorizontal) < displayRadX]
            y= y[np.abs(y-self.beamCenterVertical) < displayRadY]
            xHighRes = self.xHighRes[ np.abs(xHighRes-self.beamCenterHorizontal) < displayRadX]
            yHighRes= self.yHighRes[np.abs(yHighRes-self.beamCenterVertical) < displayRadY]
            
        if self.checkBurntRows:
            dataY = dataY[visibleUnburntRows]
            y = y[visibleUnburntRows]
            
        if self.checkBurntColumns:
            dataX = dataX[visibleUnburntColumns]
            x = x[visibleUnburntColumns]
          
        
        
        if self.plotGaussianFits:
            
            meanX = np.trapz(x*dataX,x)/np.trapz(dataX,x)
            meanY = np.trapz(y*dataY,y)/np.trapz(dataY,y)
     
            
            stdX = np.sqrt(np.trapz((x-meanX)**2*dataX,x)/np.trapz(dataX,x))
            stdY = np.sqrt(np.trapz((y-meanY)**2*dataY,y)/np.trapz(dataY,y))
    
            maxX = np.max(dataX)
            maxY = np.max(dataY)
            minPixel = np.min((self.dataImage))
            
            try:
                paramY = opt.curve_fit(ueye.gaussian, y,dataY, [maxY-minPixel, meanY, stdY*2, minPixel], bounds= ([0, self.horizontalLength/100, self.pixelSize, 0] , [255, 99*self.verticalLength/100, self.verticalLength, 255]) )[0]
            except:
                paramY = [0,meanY,stdY*2,0]
                
            try:
                paramX = opt.curve_fit(ueye.gaussian, x,dataX, [maxX-minPixel, meanX, stdX*2, minPixel], bounds= ([0, self.verticalLength/100, self.pixelSize, 0] , [255, 99*self.horizontalLength/100, self.horizontalLength, 255]) )[0]
            except:
                paramX = [0,meanX,stdX*2,0]
                
            #self.beamCenterHorizontal = paramX[1]
            self.diamX = abs(2*paramX[2])
            #self.beamCenterVertical = paramY[1]
            self.diamY = abs(2*paramY[2])
            
            
            gaussX = ueye.gaussian(xHighRes,paramX[0],paramX[1],paramX[2],paramX[3])
            gaussY = ueye.gaussian(yHighRes,paramY[0],paramY[1],paramY[2],paramY[3])
            
            #self.plotImageX.disableAutoRange()
            #self.plotImageY.disableAutoRange()
            
            self.plotImageX.plot(xHighRes,gaussX, clear = True)
            self.plotImageY.plot(gaussY, yHighRes,clear = True)
            self.plotImageX.plot(x,dataX, pen=None, symbol = 'o')
            self.plotImageY.plot(dataY,y, pen=None, symbol = 'o')
            
            #self.plotImageX.autoRange()
            #self.plotImageY.autoRange()
        else:
            
            #self.plotImageX.disableAutoRange()
            #self.plotImageY.disableAutoRange()
            
            self.plotImageX.plot(x,dataX, pen=None, symbol = 'o', clear = True)
            self.plotImageY.plot(dataY,y, pen=None, symbol = 'o', clear = True)
            
            
            #self.plotImageX.autoRange()
            #self.plotImageY.autoRange()
        
        if self.displayCameraImage:
            self.plotImage.setImage(self.dataImage.T, autoDownSample = True)
        
        self.set_text('update')
        
   
    def set_text(self, option = 'update'):
        self.displayStr = ['','','','','']
        
        
        if self.maxCounts > 250:
            self.displayStr[0] = 'Highest counts: ' + str(self.maxCounts) + '\t SATURATION\n'
        else:
            self.displayStr[0] = 'Highest counts: ' + str(self.maxCounts) + '\n'
        self.displayStr[1] = 'Exposure time: '+ str( round(self.camExposure,3) ) + ' ms\n'
        self.displayStr[2] = 'Zoom: ' + str(self.zoomValue)
        if self.applyZoom:
            self.displayStr[2] += '  (on)\n\n'
        else:
            self.displayStr[2] += '  (off)\n\n'
    
        if self.plotGaussianFits:
            self.displayStr[3] = 'Centered @ x-' + str(round(self.beamCenterHorizontal/1000,1)) + ' , y-' + str(round(self.beamCenterVertical/1000,1)) + ')  [mm]\n'
            self.displayStr[4] = 'Diam. @ 1/e^2:  x-' + str(round(self.diamX,1)) + '  y-' + str(round(self.diamY,1)) + '  [um]'
    
        if option == 'initialize':    
            self.textBox = pg.TextItem(''.join(self.displayStr))
            font = QtGui.QFont("SansSerif", 17)
            self.textBox.setFont(font)
        elif option == 'update':
            self.textBox.setText( ''.join(self.displayStr) )
            
            
    def on_gaussian_fits_checkbox_clicked(self):
        
        self.plotGaussianFits = not self.plotGaussianFits
        
        
    def on_zoom_centering_checkbox_cliked(self):
        
        self.updateZoomCenter = not self.updateZoomCenter
        
    def on_image_display_checkbox_clicked(self):
        
        self.displayCameraImage = not self.displayCameraImage
        
    def on_zoom_checkbox_clicked(self):
        
        self.applyZoom = not self.applyZoom
        self.set_text('update')
        
        
    def on_burnt_columns_checkbox_clicked(self):
        
        self.checkBurntColumns = not self.checkBurntColumns
        
        if self.checkBurntRows:
            self.checkBurntRows = not self.checkBurntRows
            
        if self.checkBurntColumns:
        
            self.dataImage = self.camHandle.acquire()
            
            maxProjectionX = np.max(self.dataImage,0)
            
            self.unburntColumns = maxProjectionX <self.countsThresholdBurntPixels
            
        
    def on_burnt_rows_checkbox_clicked(self):
        
        self.checkBurntRows = not self.checkBurntRows
        
        if self.checkBurntColumns:
            self.checkBurntColumns = not self.checkBurntColumns
            
        if self.checkBurntRows:
        
            self.dataImage = self.camHandle.acquire()
            
            maxProjectionY = np.max(self.dataImage,1)
            
            self.unburntRows = maxProjectionY <self.countsThresholdBurntPixels
        
    def on_zoom_value_edited(self):
        
        newValue = self.zoomValuetextbox.text()
        
        try:
            newValue = int(newValue)
            if newValue > 0:
                self.zoomValue = newValue
            self.set_text('update')
        except:
            pass
        
    def on_exposure_slider_adjustment(self):
        
        sliderValue =   int(self.exposureSlider.value())
        
        exposureSteps = np.logspace(np.log10(self.camExposureMin),np.log10(self.camExposureMax), self.exposureSliderNumberSteps)
        
        newExposure = exposureSteps[sliderValue]
            
        self.camHandle.set_exposure(newExposure)
        self.camExposure = newExposure
        
        self.set_text('update')
        self.update_plot()
        
    def on_save_button_pressed(self):
        
        
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        filePath = os.path.join(self.saveFolder,timeStamp)
        
        np.savez(filePath, image = self.dataImage, x = self.x, y = self.y)
        
        
    def ensure_data_folder_exists(self):
        
        dataFolderExists = os.path.isdir('./Data')
        
        if not dataFolderExists:
            os.mkdir('./Data')
            
        todayDataFolderExists = os.path.isdir(self.saveFolder)
            
        if not todayDataFolderExists:
            os.mkdir(self.saveFolder)
       
    

def connect_camera():
    """
    Connect to camera.
    
    """
    camHandle = ueye.UeyeCamera()
    
    names = camHandle.return_devices()
    
    camHandle.connect_device(names[0])

    return names[0], camHandle



def main():
    """
    Main function that is executed when running this script. Creates the app, 
    connects to the camera then display its data in rela time.
    
    """
    
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('Ueye beam profiler')
    
    
    camName, camHandle = connect_camera()
    
    ex = ueye_beam_profiler(camName, camHandle)
    app.exec_()
    camHandle.disconnect_device()


if __name__ == '__main__':
    main()