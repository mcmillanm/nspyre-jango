#from asyncio import wait_for
#from os import wait
import time
import logging
from pathlib import Path

import numpy as np
from nspyre import DataSource
from nspyre import experiment_widget_process_queue
from nspyre import StreamingList
from nspyre import nspyre_init_logger

import pyvisa
from pyvisa import ResourceManager

#import pulsestreamer # you can download the packages using pip, see swabian 8/2 documentation
#from pulsestreamer import *

from template.drivers.insmgr import MyInstrumentManager
from template.drivers.nspyre_drivers.agilent.e8257d import AgilentE8257D as AGD

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)

class FrequencyGen:
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

    def Frequency_Gen(self, RFAmp: float, RFfrequency: float):
        
        """Write code in here for diagnostics"""
        SG = AGD.SG_Connect()
        AGD.idn(AGD)

        AGD.set_rf_frequency(AGD, RFfrequency*1e9)
        AGD.get_rf_frequency(AGD)

        AGD.set_rf_amplitude(AGD, RFAmp)
        AGD.get_rf_amplitude(AGD)

        AGD.get_rf_toggle(AGD)
        AGD.set_rf_toggle(AGD, 'OFF')
        AGD.get_rf_toggle(AGD)
        
        """Args:
            dataset: name of the dataset to push data to
            t_i (float): start time (ns)
            t_f (float): stop time (ns)
            num_points (int): number of points between start-stop (inclusive)
            iterations: number of times to repeat the experiment
        """
        # connect to the instrument server
        # connect to the data server and create a data set, or connect to an
        # existing one with the same name if it was created earlier.

        #with MyInstrumentManager() as mgr, DataSource(dataset) as test_data:
            
           # swab_driver = mgr.swabian # acsess modules in 'SwabianPS82.py' by using swab_driver.[whatever module want]
            #ps = pulsestreamer.PulseStreamer("169.254.8.2") # control the pulse streamer by using ps.[whatever module you want]
                    
if __name__ == '__main__':
    exp = FrequencyGen()
    exp.Frequency_Gen()