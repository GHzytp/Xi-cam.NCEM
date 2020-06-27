import time
import dask
import dask.array as da
from pathlib import Path
import numpy as np
import h5py

import event_model


def ingest_NCEM_4DC(paths):
    assert len(paths) == 1
    path = paths[0]

    file_handle = h5py.File(path, 'r')

    # Compose run start
    run_bundle = event_model.compose_run()  # type: event_model.ComposeRunBundle
    start_doc = run_bundle.start_doc
    start_doc["sample_name"] = Path(paths[0]).resolve().stem

    #metadata = {}
    #start_doc = metadata

    yield 'start', start_doc

    num_sum = 10

    num_t = 2000  #_num_t(file_handle)
    first_frame = _get_slice(file_handle, 0, num_sum).compute()
    shape = first_frame.shape
    dtype = first_frame.dtype

    ## Diff patterns only
    t0 = time.time()
    dask_data = da.stack([da.from_delayed(_get_slice(file_handle, t, t+num_sum), shape=shape, dtype=dtype)
                         for t in range(num_t)])
    print('time = {}'.format(time.time() - t0))

    ## 4D
    # scan_dimensions = (file_handle['electron_events/scan_positions'].attrs['Ny'],
    #                    file_handle['electron_events/scan_positions'].attrs['Nx'])
    # scan_dimensions = (50, 50)
    # # Treat as 4D
    # XX, YY = np.mgrid[0:scan_dimensions[0], 0:scan_dimensions[1]]
    # t0 = time.time()
    # print('start ingesting')
    # dask_data = da.stack([da.from_delayed(delayed_getDenseFrame3(file_handle, x, y), shape=shape, dtype=dtype)
    #                       for x, y in zip(XX.ravel(), YY.ravel())])
    # dask_data = dask_data.reshape(*scan_dimensions, 576, 576)
    # print(dask_data.shape)
    # print('time = {}'.format(time.time() - t0))

    # Compose descriptor
    source = 'NCEM'
    # Treat as 3D
    frame_data_keys = {'raw': {'source': source,
                               'dtype': 'number',
                               'shape': (num_t, *shape)}}
    # Treat as 4D
    # frame_data_keys = {'raw': {'source': source,
    #                            'dtype': 'number',
    #                            'shape': dask_data.shape}}

    frame_stream_name = f'primary'

    frame_stream_bundle = run_bundle.compose_descriptor(data_keys=frame_data_keys,
                                                        name=frame_stream_name,
                                                        configuration={}
                                                        )
    yield 'descriptor', frame_stream_bundle.descriptor_doc

    # NOTE: Resource document may be meaningful in the future. For transient access it is not useful
    # # Compose resource
    # resource = run_bundle.compose_resource(root=Path(path).root, resource_path=path, spec='NCEM_DM', resource_kwargs={})
    # yield 'resource', resource.resource_doc

    # Compose datum_page
    # z_indices, t_indices = zip(*itertools.product(z_indices, t_indices))
    # datum_page_doc = resource.compose_datum_page(datum_kwargs={'index_z': list(z_indices), 'index_t': list(t_indices)})
    # datum_ids = datum_page_doc['datum_id']
    # yield 'datum_page', datum_page_doc

    yield 'event', frame_stream_bundle.compose_event(data={'raw': dask_data},
                                                     timestamps={'raw': time.time()})

    yield 'stop', run_bundle.compose_stop()
    print('Done ingesting')


def _num_t(file_hdl):
    """ The number of diffraction patterns
    """
    return file_hdl['electron_events/frames'].shape[0]


def _parse_file(self):
    """ Read the meta data in the file needed to interpret the electron strikes.

    """

    if 'electron_events' in self.fid:
        self.frames = self.fid['electron_events/frames']
        self.scan_positions = self.fid['electron_events/scan_positions']

        self.scan_dimensions = [self.scan_positions.attrs[x] for x in ['Ny', 'Nx']]
        self.frame_dimensions = [self.frames.attrs[x] for x in ['Ny', 'Nx']]
        self.num_frames = self.frames.shape[0]
    return

@dask.delayed
def _get_slice(file_hdl, start, end):
    """ Get a dense frame summed from the start frame number to the end frame number.

    To do: Allow user to sum frames in a square ROI using start and end as tuples.

    Parameters
    ----------
    start : int
        If int treat as raveled array and sum. If tuple then treat the array as a 4D array and
        start is the lower left corner of a box to sum in.

    end : int
        If int treat as raveled array and sum. If tuple then treat the array as a 4D array and
        start is the upper right corner of a box to sum in.

    Returns
    -------
        : np.ndarray
            An ndarray of the summed counts. np.dtype is uint32. Shape is frame_dimensions
    """
    #print('get_slice start {}'.format(start))
    dp = np.zeros(576*576, dtype=np.uint16)
    for ii, ev in enumerate(file_hdl['electron_events/frames'][start:end]):
        dp[ev] += 1
    return dp.reshape(576, 576)

@dask.delayed
def delayed_getDenseFrame3(file_hdl, x, y):
    dp = np.zeros(576*576, dtype='<u4')
    z = np.ravel_multi_index((x,y), (50,50))
    ev = file_hdl['electron_events/frames'][z]
    dp[ev] += 1
    return dp.reshape(576, 576)

#if __name__ == "__main__":
#    print(list(ingest_NCEM_4DC(["C:/Users/linol/Data/data_scan218_electrons.4dc"])))
