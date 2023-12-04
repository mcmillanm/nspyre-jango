"""
This is an experiment to run Rabi on Jasper using new CountsVsDV experiment class

Copyright (c) September 2023, C. Egerstrom
All rights reserved.

This work is licensed under the terms of the 3-Clause BSD license.
For a copy, see <https://opensource.org/licenses/BSD-3-Clause>.
"""
import numpy as np
from nspyre import StreamingList

from experiments.General.generalExperiments import CountsVsDV_Experiment
from experiments.customUtils import setupIters, setupAPD, setupSigGen
from experiments.PulsePatterns import Pulses, convertSecKwargsToNanosec, convertSecArgsToNanosec, convertRLEtoSeq #, convertDigRLEtoSeq #DEBUG

from drivers.ni.nidaqTimingFromSwab import TreelessNIDAQ


class RabiMeasurement(CountsVsDV_Experiment):

    def __init__(self, queue_to_exp, queue_from_exp): #Need queue arguments to get relevant queues from GUI's ProcessRunner
        super().__init__(xNickname='taus', yNicknames=['mwCounts', 'noMwCounts'], 
                         expMethodNickname='rabi', expNameForLogsAndSaves='Rabi', 
                         queue_to_exp=queue_to_exp, queue_from_exp=queue_from_exp)


    def expSetupMethod(self, gw, maxIters:int, 
                        minMwTime: float, maxMwTime: float, numMWtimes: int, rfFreq:float, rfPower: float,  
                        **kwargs):
        #Turn the sig-gen on 
        setupSigGen(gw, rfFreq, rfPower)
        #Turn the APD on
        setupAPD(gw)
        #set up iterator
        iters = setupIters(maxIters)
        #setup data storage structures
        Xs = np.linspace(*convertSecArgsToNanosec(minMwTime, maxMwTime), numMWtimes, dtype=int).tolist() #make these into int's of ns's here for convenience
        Ys = [[StreamingList() for X in Xs] for yNickname in self.yNicknames]
        return(Xs, Ys, iters)


    def expLoopMethod(self, gw, X, samplingFreq,
                      aomRiseLag: float, readoutTime:float, initTime:float, 
                      aomFallLagAndISC:float, bufferTime:float, aomV:float, **kwargs):
        #Start streaming the sequence that every datapoint will use

        gw.swabian.ps.constant( [(), 0,0]) #turn the Swab off before starting tasks so they're synced properly

        swabRLE = Pulses().rabiWithBackground(tauTime = X, maxTauTime=self.Xs[-1], 
                        **convertSecKwargsToNanosec(aomRiseLagTime=aomRiseLag, 
                            readOutTime=readoutTime, extraInitLaserTime=initTime,
                            aomFallLagAndISC=aomFallLagAndISC,  bufferTime=bufferTime), aomV=aomV)
        numSamplesPerDC = 4 #both read windows and deadtimes
        
        #for a given sampling freq, you need to take numSamplesPerDutyCycle*SamplingTime/DutyCycle
        #here we round that fraction up (floor div+1) and use 1/sampleFreq as SamplingTime
        #and plus 2 because of start/end buffers?!? Not entirely sure if necessary but should have minimum timing overhead
        num_samples = 2+numSamplesPerDC*int(1+1e9//(convertRLEtoSeq(swabRLE).getDuration()*samplingFreq))
        #print(type(num_samples)) #DEBUG

        with TreelessNIDAQ() as NIDAQ:
            NIDAQ.start_read_tasks_swabTimed(num_samples)
            gw.swabian.runSequenceInfinitely(swabRLE)
            counts, flags = NIDAQ.read_samples(num_samples)
        
        #print(counts, flags) #DEBUG
        #for flag in flags: #DEBUG
        #    print(flag) #DEBUG
        for i,flag in enumerate(flags[numSamplesPerDC-1::numSamplesPerDC]):
            if flag != 1: #TODO: Make this more robust in a TTL Flag is lost/missed
                raise(ValueError(f'WARNING! Flag was not detected at {i*(numSamplesPerDC+1)}, instead {flag}'))
        noMWcounts, mwCounts = counts[0:numSamplesPerDC-1+i*numSamplesPerDC:numSamplesPerDC], counts[2:numSamplesPerDC-1+i*numSamplesPerDC:numSamplesPerDC] #go until last Flag signal
        return(int(np.sum(mwCounts)), int(np.sum(noMWcounts)))
        



