import numpy as np
import time
import math
from itertools import cycle
import logging
import scipy as sp
from scipy import signal
import datetime as Dt

from rpyc.utils.classic import obtain 

# nidaqmx STAYS SAME
import nidaqmx

#CHECK FOR ADDITIONAL CONSTANTS
from nidaqmx.constants import Edge, READ_ALL_AVAILABLE, TaskMode, TriggerType, AcquisitionType
from nidaqmx.stream_readers import CounterReader
from nidaqmx.stream_readers import AnalogSingleChannelReader 

from contextlib import ExitStack

class NIDAQ():

    def __init__(self):
        pass
        
        # USB 6343
        self.sampling_rate = 4e-3
        self.period = 1 / self.sampling_rate
        self.reader_stream = []

        self.clk_channel = '/Dev1/PFI2' # ctr 2
        self.dev_channel = '/Dev1/PFI0' # ctr 1


    def read_ctrs_ext_clk(self, acq_rate, num_samples):

        # applying user's acquisition rate
        self.sampling_rate = acq_rate
        self.period = 1 / self.sampling_rate

        # empty counts
        counts = []

        # creating DAQ task  
        self.read_task = nidaqmx.Task()
        
        # adding digital input channel as counter (APD)
        self.read_task.ci_channels.add_ci_count_edges_chan(f'/Dev1/ctr1')

        # connecting physical input to virtual counter
        self.read_task.ci_channels.all.ci_count_edges_term = '/Dev1/PFI0'

        # setting up timing clock (external)
        self.read_task.timing.cfg_samp_clk_timing(
                                self.sampling_rate,
                                source = '/Dev1/PFI2',
                                active_edge = nidaqmx.constants.Edge.RISING,
                                sample_mode = nidaqmx.constants.AcquisitionType.FINITE,
                                samps_per_chan = num_samples
        )

        # creating counter stream object for counting
        self.reader_stream = CounterReader(self.read_task.in_stream)
        
        # starting counting task
        self.read_task.start()

        # reading counter out starting with the buffer
        raw_counts = np.zeros(num_samples, dtype=np.uint32) + 1
        self.reader_stream.read_many_sample_uint32(
                                raw_counts,
                                number_of_samples_per_channel = nidaqmx.constants.READ_ALL_AVAILABLE,
                                timeout = 0 #num_samples * self.period + 1
        )
            
        self.read_task.stop()
        self.read_task.close()
            
        # calculate difference in counts between each period
        counts.append(np.diff(raw_counts))
        return np.array(counts)

       


    
