from xicam.plugins import QWidgetPlugin
from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView
from xicam.core.data import NonDBHeader

from pyqtgraph import ImageView, PlotItem
import pyqtgraph as pg

from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtCore import QRect, QRectF

import numpy as np

class FFTViewerPlugin(QWidgetPlugin): #needs QWidget also?
    def __init__(self, header: NonDBHeader = None, field: str = 'primary', toolbar: QToolBar = None, *args, **kwargs):
        
        #super(FFTViewerPlugin, self).__init__(*args, **kwargs)
        super(FFTViewerPlugin, self).__init__(**kwargs) #Same as NCEMviewer
        #super(FFTViewerPlugin, self).__init__(*args, *kwargs) #same as FFTviewer although this may not be correct
        
        self.Rimageview = DynImageView()
        self.Fimageview = ImageView()
        
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.Rimageview)
        self.layout().addWidget(self.Fimageview)
        
        #Add ROI to real image
        self.Rroi = pg.RectROI(pos=(0, 0), size=(100, 100), translateSnap=True, snapSize=1, scaleSnap=True)
        self.Rroi.sigRegionChanged.connect(self.updateFFT)
        Rview = self.Rimageview.view  # type: pg.ViewBox
        Rview.addItem(self.Rroi)
        self.Rroi.setZValue(10)
        
        # Add axes to the main data
        #self.axesItem = PlotItem()
        #self.axesItem.setLabel('bottom', u'q ()')  # , units='s')
        #self.axesItem.setLabel('left', u'q ()')
        #self.axesItem.axes['left']['item'].setZValue(10)
        #self.axesItem.axes['top']['item'].setZValue(10)
        #if 'view' not in kwargs: kwargs['view'] = self.axesItem
        #self.Rimageview = DynImageView(view=self.axesItem)
        
        #Two Dynamic image views (maybe only need 1 for the main data. The FFT can be an ImageView()
        #self.Rimageview = DynImageView()
        #self.Fimageview = ImageView()
        # Keep Y-axis as is
        #self.Rimageview.view.invertY(True)
        #self.Fimageview.view.invertY(True)
        #self.Rimageview.imageItem.setOpts(axisOrder='col-major')
        #self.Fimageview.imageItem.setOpts(axisOrder='col-major')
        
        
        #self.layout().addWidget(self.Rimageview)
        #self.layout().addWidget(self.Fimageview)
        
        
        
        
        '''
        # Setup axes reset button 
        self.resetAxesBtn = QPushButton('Reset Axes')
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.resetAxesBtn.sizePolicy().hasHeightForWidth())
        self.resetAxesBtn.setSizePolicy(sizePolicy)
        self.resetAxesBtn.setObjectName("resetAxes")
        self.ui.gridLayout.addWidget(self.resetAxesBtn, 2, 1, 1, 1)
        self.resetAxesBtn.clicked.connect(self.autoRange)

        # Setup LUT reset button
        self.resetLUTBtn = QPushButton('Reset LUT')
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.resetLUTBtn.sizePolicy().hasHeightForWidth())
        # self.resetLUTBtn.setSizePolicy(sizePolicy)
        # self.resetLUTBtn.setObjectName("resetLUTBtn")
        self.ui.gridLayout.addWidget(self.resetLUTBtn, 3, 1, 1, 1)
        self.resetLUTBtn.clicked.connect(self.autoLevels)

        # Hide ROI button and rearrange
        self.ui.roiBtn.setParent(None)
        self.ui.gridLayout.addWidget(self.ui.menuBtn, 1, 1, 1, 1)
        self.ui.gridLayout.addWidget(self.ui.graphicsView, 0, 0, 3, 1)

        # Setup coordinates label
        self.coordinatesLbl = QLabel('--COORDINATES WILL GO HERE--')
        self.ui.gridLayout.addWidget(self.coordinatesLbl, 3, 0, 1, 1, alignment=Qt.AlignHCenter)
        '''
        
        # Set header
        if header: self.setHeader(header, field)
    
    def updateFFT(self, data):
        '''Update the FFT diffractogram based on the Real space
        ROI location and size
        
        '''
        #msg.logMessage('0 = {}'.format(int(self.Rroi.pos().x())))
        #msg.logMessage('1 = {}'.format(int(self.Rroi.pos().y())))
        #msg.logMessage('2 = {}'.format(int(self.Rroi.size().x())))
        #msg.logMessage('3 = {}'.format(int(self.Rroi.size().y())))
        #x0 = int(self.Rroi.pos().x())
        #x1 = int(self.Rroi.pos().x()) + int(self.Rroi.size().x())
        #y0 = int(self.Rroi.pos().y())
        #y1 = int(self.Rroi.pos().y()) + int(self.Rroi.size().y())
        #msg.logMessage('type data = {}'.format(type(data)))
        
        x0 = 0
        x1 = 300
        y0 = 0
        y1 = 300
        
        temp = data[x0:x1,y0:y1]
        fft = np.fft.fft2(temp)
        #fft = np.fft.fft2(data[int(self.Rroi.pos().x()):int(self.Rroi.pos().x() + self.Rroi.size().x()),
        #                       int(self.Rroi.pos().y()):int(self.Rroi.pos().y() + self.Rroi.size().y())] )
        self.Fimageview.setImage(np.log(np.abs(np.fft.fftshift(fft)) + 1))
    
    def setHeader(self, header: NonDBHeader, field: str, *args, **kwargs):
        self.header = header
        self.field = field
        # make lazy array from document
        data = None
        try:
            data = header.meta_array(field)
        except IndexError:
            msg.logMessage('Header object contained no frames with field {field}.', msg.ERROR)

        if data:
            # data = np.squeeze(data) #test for 1D spectra
            if data.ndim > 1:
                # kwargs['transform'] = QTransform(0, -1, 1, 0, 0, data.shape[-2])
                #NOTE PAE: for setImage:
                #   use setImage(xVals=timeVals) to set the values on the slider for 3D data
                try:
                    #Unified meta data for pixel scale and units
                    scale0 = (header.descriptors[0]['PhysicalSizeX'],header.descriptors[0]['PhysicalSizeY'])
                    units0 = (header.descriptors[0]['PhysicalSizeXUnit'],header.descriptors[0]['PhysicalSizeYUnit'])
                except:
                    scale0 = [1, 1]
                    units0 = ['', '']
                    #msg.logMessage{'NCEMviewer: No pixel size or units detected'}
                self.Rimageview.setImage(img=data, scale=scale0, *args, **kwargs)
                
                # TODO: Need to add axesitem to the DynImageView
                #self.axesItem.setLabel('bottom', text='X', units=units0[0])
                #self.axesItem.setLabel('left', text='Y', units=units0[1])
                
                #Update the FFT of the image when new data is shown
                self.updateFFT(data)
            #else:
            #    msg.logMessage('Cant load 1D data.')
