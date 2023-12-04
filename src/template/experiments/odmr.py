"""
This is example script demonstrates most of the basic functionality of nspyre.
"""
import time
import logging
from pathlib import Path

import numpy as np
from nspyre import DataSource
from nspyre import experiment_widget_process_queue
from nspyre import StreamingList
from nspyre import nspyre_init_logger

from template.drivers.nspyre_drivers.agilent.e8257d import AgilentE8257D as AGD
from template.drivers.nspyre_drivers.ni.ni_photonCounting import NIDAQ as DAQ
import pulsestreamer as PS

from template.drivers.insmgr import MyInstrumentManager

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)

class SpinMeasurements:
    """Spin measurement experiments."""

    def __init__(self, queue_to_exp=None, queue_from_exp=None):
        """
        Args:
            queue_to_exp: A multiprocessing Queue object used to send messages
                to the experiment from the GUI.
            queue_from_exp: A multiprocessing Queue object used to send messages
                to the GUI from the experiment.
        """
        self.queue_to_exp = queue_to_exp
        self.queue_from_exp = queue_from_exp

    def __enter__(self):
        """Perform experiment setup."""
        # config logging messages
        # if running a method from the GUI, it will be run in a new process
        # this logging call is necessary in order to separate log messages
        # originating in the GUI from those in the new experiment subprocess
        nspyre_init_logger(
            log_level=logging.INFO,
            log_path=_HERE / '../logs',
            log_path_level=logging.DEBUG,
            prefix=Path(__file__).stem,
            file_size=10_000_000,
        )
        _logger.info('Created SpinMeasurements instance.')

    def __exit__(self):
        """Perform experiment teardown."""
        _logger.info('Destroyed SpinMeasurements instance.')

    def odmr_sweep(self,
        dataset: str,
        start_freq: float,
        stop_freq: float,
        power: float,
        num_points: int,
        iterations: int,
        period: int
    ):
        """Run a fake ODMR (optically detected magnetic resonance)
        PL (photoluminescence) sweep over a set of microwave frequencies.

        Args:
            dataset: name of the dataset to push data to
            start_freq (float): start frequency
            stop_freq (float): stop frequency
            num_points (int): number of points between start-stop (inclusive)
            iterations: number of times to repeat the experiment
        """
        # connect to the instrument server
        # connect to the data server and create a data set, or connect to an
        # existing one with the same name if it was created earlier.

        SG = AGD.SG_Connect()
        AGD.idn(AGD)

        with MyInstrumentManager() as mgr, DataSource(dataset) as odmr_data:
            
            odmr_driver = mgr.odmr_driver
            ps = PS.PulseStreamer("169.254.8.2")
            clk_sequence = ps.createSequence()
            patt_d_ch0 = [(100, 1), (100, 0)]

            # set the signal generator amplitude for the scan (dBm).

            AGD.set_rf_amplitude(AGD, power)

            # frequencies that will be swept over in the ODMR measurement

            frequencies = np.linspace(start_freq, stop_freq, num_points)

            # for storing the experiment data
            # list of numpy arrays of shape (2, num_points)

            signal_sweeps = StreamingList()
            background_sweeps = StreamingList()

            for i in range(iterations):

                # photon counts corresponding to each frequency
                # initialize to NaN

                sig_counts = np.empty(num_points)
                sig_counts[:] = np.nan
                signal_sweeps.append(np.stack([frequencies/1e9, sig_counts]))
                bg_counts = np.empty(num_points)
                bg_counts[:] = np.nan
                background_sweeps.append(np.stack([frequencies/1e9, bg_counts]))

                # sweep counts vs. frequency.

                for f, freq in enumerate(frequencies):

                    # access the signal generator driver on the instrument server and set its frequency.
                    
                    AGD.set_rf_frequency(AGD, freq)
                    AGD.set_rf_toggle(AGD, 'ON')
                    
                    # read the number of photon counts received by the photon counter.
                    
                    '''Add DAQ counts, not odmr_driver.counts(0.005)'''
                    clk_sequence.setDigital(0, patt_d_ch0)
                    ps.stream(clk_sequence, PS.PulseStreamer.REPEAT_INFINITELY)

                    print(signal_sweeps[-1][1])
                    print(DAQ.read_ctrs_ext_clk(DAQ, period, 2)[0])
                    signal_sweeps[-1][1][f] = DAQ.read_ctrs_ext_clk(DAQ, period, 5)[0][0]
                    
                    # notify the streaminglist that this entry has updated so it will be pushed to the data server
                    
                    signal_sweeps.updated_item(-1)

                    # set the signal generator off for a background noise signal
                    
                    AGD.set_rf_toggle(AGD, 'OFF')
                    '''Add DAQ counts, not odmr_driver.counts(0.005)'''
                    background_sweeps[-1][1][f] = DAQ.read_ctrs_ext_clk(DAQ, period, 2)
                    background_sweeps.updated_item(-1)

                    
                    # save the current data to the data server.
                    odmr_data.push({'params': {'start': start_freq, 'stop': stop_freq, 'power': power, 'num_points': num_points, 'iterations': iterations},
                                    'title': 'Optically Detected Magnetic Resonance',
                                    'xlabel': 'Frequency (GHz)',
                                    'ylabel': 'Counts',
                                    'datasets': {'signal' : signal_sweeps,
                                                'background': background_sweeps}
                    })

                    AGD.get_rf_toggle(AGD)

                    if experiment_widget_process_queue(self.queue_to_exp) == 'stop':
                        # the GUI has asked us nicely to exit
                        return

if __name__ == '__main__':
    exp = SpinMeasurements()
    exp.odmr_sweep('odmr', 3e9, 4e9, 101, 50)
    #exp.odmr_sweep('odmr', 3e9, 4e9, 101, 50)
