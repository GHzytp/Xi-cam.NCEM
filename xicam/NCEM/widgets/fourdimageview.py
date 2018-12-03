from xicam.plugins import QWidgetPlugin
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtCore import QRect, QRectF
from xicam.core.data import NonDBHeader
import pyqtgraph as pg
import numpy as np
from ncempy.io import dm
from pathlib import Path
from xicam.gui.widgets.dynimageview import DynImageView

class FourDImageView(QWidgetPlugin,QWidget):
    def __init__(self, header: NonDBHeader = None, field: str = 'primary', toolbar: QToolBar = None, *args, **kwargs):
        
        super(FourDImageView, self).__init__(*args, *kwargs)
        self.DPimageview = pg.ImageView()
        self.RSimageview = pg.ImageView()
        
        self.DPimageview.setPredefinedGradient('viridis')
        self.RSimageview.setPredefinedGradient('viridis')
        
        #Using DynImageView rotates the data and the ROI does not work correctly.
        #self.DPimageview = DynImageView()
        #self.RSimageview = DynImageView()
        
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.DPimageview)
        self.layout().addWidget(self.RSimageview)
        
        self.DProi = pg.RectROI(pos=(0, 0), size=(10, 10), translateSnap=True, snapSize=1, scaleSnap=True)
        self.RSroi = pg.RectROI(pos=(0, 0), size=(2, 2), translateSnap=True, snapSize=1, scaleSnap=True)
        self.DProi.sigRegionChanged.connect(self.updateRS)
        self.RSroi.sigRegionChanged.connect(self.updateDP)

        DPview = self.DPimageview.view  # type: pg.ViewBox
        DPview.addItem(self.DProi)
        RSview = self.RSimageview.view  # type: pg.ViewBox
        RSview.addItem(self.RSroi)
        
        # Set header
        if header: self.setHeader(header, field)
        
    def setData(self, data):
        '''Set the data and the limits of the ROIs
        
        '''
        self.data = data
        
        self.DPlimit = QRectF(0,0,data.shape[2],data.shape[3])
        self.RSlimit = QRectF(0,0,data.shape[0],data.shape[1])

        self.DProi.maxBounds = self.DPlimit
        self.RSroi.maxBounds = self.RSlimit
        
        self.updateRS()
        self.updateDP()

    def updateRS(self):
        '''Update the diffraction space image based on the Real space
        ROI location and size
        
        '''
        self.RSimageview.setImage(np.log(np.sum(self.data[:, :,int(self.DProi.pos().x()):int(self.DProi.pos().x() + self.DProi.size().x()),int(self.DProi.pos().y()):int(self.DProi.pos().y() + self.DProi.size().y())], axis=(3, 2),dtype=np.float32) + 1))
    
    def updateDP(self):
        '''Update the real space image based on the diffraction space
        ROI location and size.
        
        '''
        self.DPimageview.setImage(np.sum(self.data[int(self.RSroi.pos().x()):int(self.RSroi.pos().x() + self.RSroi.size().x()),int(self.RSroi.pos().y()):int(self.RSroi.pos().y() + self.RSroi.size().y()), :, :], axis=(1, 0),dtype=np.float32))
    
    def setHeader(self, header: NonDBHeader, field: str, *args, **kwargs):
        self.header = header
        self.field = field
        # make lazy array from document
        data = None
        try:
            data = header.meta_array(field)
        except IndexError:
            msg.logMessage('Header object contained no frames with field ''{field}''.', msg.ERROR)

        if data:
            data2 = self.tempGetData(self)
            #super(FourDImageView, self).setData(data2, *args, **kwargs)
            self.setData(data2)
    
    def tempGetData(self,*args,**kwargs):
        #Try to load the data
        dPath = Path(r'C:/Users/Peter.000/Data/Te NP 4D-STEM')
        fPath = Path('07_45x8 ss=5nm_spot11_CL=100 0p1s_alpha=4p63mrad_bin=4_300kV.dm4')
        with dm.fileDM((dPath / fPath).as_posix()) as dm1:
            try:
                scanI = int(dm1.allTags['.ImageList.2.ImageTags.Series.nimagesx'])
                scanJ = int(dm1.allTags['.ImageList.2.ImageTags.Series.nimagesy'])
                im1 = dm1.getDataset(0)
                numkI = im1['data'].shape[2]
                numkJ = im1['data'].shape[1]

                data = im1['data'].reshape([scanJ,scanI,numkJ,numkI])
            except:
                raise
                print('Data is not a 4D DM3 or DM4 stack.')
        return data
    
'''

if __name__ == '__main__':
    #Try to load the data
    dPath = Path(r'C:/Users/Peter.000/Data/Te NP 4D-STEM')
    fPath = Path('07_45x8 ss=5nm_spot11_CL=100 0p1s_alpha=4p63mrad_bin=4_300kV.dm4')
    with dm.fileDM((dPath / fPath).as_posix()) as dm1:
        try:
            scanI = int(dm1.allTags['.ImageList.2.ImageTags.Series.nimagesx'])
            scanJ = int(dm1.allTags['.ImageList.2.ImageTags.Series.nimagesy'])
            im1 = dm1.getDataset(0)
            numkI = im1['data'].shape[2]
            numkJ = im1['data'].shape[1]

            data = im1['data'].reshape([scanJ,scanI,numkJ,numkI])
        except:
            raise
            print('Data is not a 4D DM3 or DM4 stack.')
        
    qapp = QApplication([])

    fdview = FourDImageView()
    fdview.show()
    
    #data = np.fromfunction(lambda x, y, kx, ky: (x - kx) ** 2 + (y - ky) ** 2, (20, 20, 512, 512))

    fdview.setData(data)

    qapp.exec_()
    
'''
