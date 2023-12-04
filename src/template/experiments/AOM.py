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
import matplotlib.pyplot as plt

import pulsestreamer # you can download the packages using pip, see swabian 8/2 documentation
from pulsestreamer import *

from template.drivers.nspyre_drivers.ni.nidaqTimingFromSwab import TreelessNIDAQ
from template.drivers.insmgr import MyInstrumentManager

_HERE = Path(__file__).parent
_logger = logging.getLogger(__name__)

class AOMPulse:
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

    def AOM_pulse(self, dataset: str, t_i: float, t_f: float, num_points: int, iterations: int):
        
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

        with MyInstrumentManager() as mgr, DataSource(dataset) as test_data:
            
            swab_driver = mgr.swabian # acsess modules in 'SwabianPS82.py' by using swab_driver.[whatever module want]
            ps = pulsestreamer.PulseStreamer("169.254.8.2") # control the pulse streamer by using ps.[whatever module you want]
            
            ps.constant([(), 0, 0]) # Sets the streamer to a constant output of 0 if Output State fails

            AOMsequence = ps.createSequence() # create the sequence class
            patt_d_ch0 = [] # creates an empty sequence
            time_steps = np.linspace(t_i, t_f, num_points-1) # creates a list of desired times

            for i in range(num_points-1): #builds the pulse sequence based on numbe○r of desired data-points at each delay time, start time (t_i) and end time (t_f)
                
                patt_d_ch0.append((time_steps[i],1)) # streams (on) for desired time/data-point
                patt_d_ch0.append((40e3,0)) # pause (off) for 25 milli-seconds
            
            AOMsequence.setDigital([0,1], patt_d_ch0) # loads pulse sequence on desired digital channel

            '''Use ps.reset() in case the pulse streamer doesnt turn off, then click 'run' again in the gui'''

            signal = StreamingList()
            time_sweeps = StreamingList()

            with TreelessNIDAQ() as NIDAQ:

                for i in range(iterations):

                    sig_counts = np.empty(num_points-1)
                    sig_counts[:] = np.nan
                    time_sweeps.append(time_steps*1e-9)
                    time_sweeps.append(sig_counts)

                    NIDAQ.start_read_tasks_swabTimed(num_points)
                    ps.stream(AOMsequence, n_runs = 2, final = OutputState([],0,0))
                    counts, flags = NIDAQ.read_samples(num_points)

                    for j in range(len(time_steps)):
                        
                        time_sweeps[-1][j] = counts[j]
                        time_sweeps.updated_item(-1)
                        #print(time_sweeps)
                        test_data.push({'params': {'start': t_i, 'stop': t_f, 'num_points': num_points, 'iterations': iterations},
                                    'title': 'Counts vs. Laser Exposure Time (ns)',
                                    'xlabel': 'Pulse Duration (ns)',
                                    'ylabel': 'Counts',
                                    'datasets': {'signal' : time_sweeps}
                    
                    })
        #plt.plot(time_steps, counts)
        #plt.show()
                    
if __name__ == '__main__':
    exp = AOMPulse()
    exp.AOM_pulse('test')
    