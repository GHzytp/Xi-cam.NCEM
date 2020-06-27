
import numpy as np

from xicam.gui.widgets.dynimageview import DynImageView


class NCEMImageView(DynImageView):
    def __init__(self, *args, **kwargs):
        super(NCEMImageView, self).__init__(*args, **kwargs)

    def quickMinMax(self, data):
        return 0, 1
