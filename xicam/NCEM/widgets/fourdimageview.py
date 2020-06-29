from pyqtgraph import PlotItem
from qtpy.QtWidgets import *

from xicam.core import msg
from xicam.gui.widgets.dynimageview import DynImageView
from xicam.gui.widgets.imageviewmixins import CatalogView, FieldSelector, StreamSelector, ExportButton, BetterButtons
from .ncemimageview import NCEMImageView
from xicam.plugins import QWidgetPlugin
from .NCEMViewerPlugin import NCEMViewerPlugin

import pyqtgraph as pg

import time
import dask
import dask.array as da
from pathlib import Path
import numpy as np
import h5py


class fourdimageview(CatalogView, QWidgetPlugin):

    def __init__(self, catalog, stream: str = 'primary', field: str = 'raw',
                 toolbar: QToolBar = None, *args, **kwargs):

        self.stream = stream
        self.field = field
        self.catalog = catalog

        super(fourdimageview, self).__init__(*args, *kwargs)

        if catalog:
            self.setCatalog(catalog, stream=stream, field=field)

        # Using DynImageView rotates the data and the ROI does not work correctly.
        self.RSimageview = NCEMImageView()
        self.DPimageview = NCEMImageView()

        self.RSimageview.setImage(np.zeros((100, 100), dtype=np.uint32))
        self.DPimageview.setImage(np.zeros((576, 576), dtype=np.uint32))

        # Keep Y-axis as is
        self.DPimageview.view.invertY(True)
        self.RSimageview.view.invertY(True)
        self.DPimageview.imageItem.setOpts(axisOrder='col-major')
        self.RSimageview.imageItem.setOpts(axisOrder='col-major')
                
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
        
    def setData(self, data):
        """ Set the data and the limits of the ROIs

        """
        self.data = data

        self.DPlimit = QRectF(0,0,data.shape[2],data.shape[3])
        self.RSlimit = QRectF(0,0,data.shape[0],data.shape[1])

        self.DProi.maxBounds = self.DPlimit
        self.RSroi.maxBounds = self.RSlimit
        
        self.updateRS()
        self.updateDP()

    def updateRS(self):
        """ Update the diffraction space image based on the Real space
        ROI location and size

        """
        #self.RSimageview.setImage(np.log(np.sum(self.data[:, :, int(self.DProi.pos().x()):int(self.DProi.pos().x() + self.DProi.size().x()),int(self.DProi.pos().y()):int(self.DProi.pos().y() + self.DProi.size().y())], axis=(3, 2),dtype=np.float32) + 1))
        dd = self.data_4D[:, :, int(self.DProi.pos().x()):int(self.DProi.pos().x() + self.DProi.size().x()),
                          int(self.DProi.pos().y()):int(self.DProi.pos().y() + self.DProi.size().y())]
        dd2 = dd.sum(axis=(2, 3))
        im = dd2.compute()
        self.RSimageview.setImage(im)

    def updateDP(self):
        """ Update the real space image based on the diffraction space
        ROI location and size.

        """
        #self.DPimageview.setImage(np.sum(self.data[int(self.RSroi.pos().x()):int(self.RSroi.pos().x() + self.RSroi.size().x()),int(self.RSroi.pos().y()):int(self.RSroi.pos().y() + self.RSroi.size().y()), :, :], axis=(1, 0),dtype=np.float32))
        dd = self.data_4D[int(self.RSroi.pos().x()):int(self.RSroi.pos().x() + self.RSroi.size().x()),
             int(self.RSroi.pos().y()):int(self.RSroi.pos().y() + self.RSroi.size().y()), :, :]
        im = dd.sum(axis=(0, 1)).compute()
        self.DPimageview.setImage(im)
