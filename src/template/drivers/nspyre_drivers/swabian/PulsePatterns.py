'''Pulse sequences for many common spin physics measurements using a Swabian, and their component building-block pulses
Now using a treeless-DAQ, which means more timing needs to be provided by the Swab
Copyright (c) Nov 2023, C. Egerstrom
Based on previous work by C.Eger and D. Mark
All rights reserved.

This work is licensed under the terms of the 3-Clause BSD license.
For a copy, see <https://opensource.org/licenses/BSD-3-Clause>.
'''
from pulsestreamer import Sequence



def convertDigRLEtoSeq(RLEseq):
    '''Converts sequences of the form [ (Duration in ns, [Dig Chans to Turn On], A0, A1), (Dur in ns, [Dig Chans On], A0, A1), ...]
    type sequences to Swabian Sequences (mostly to aid with plotting). IGNORES ANALOG OUTPUTS'''
    RLEusedChans = set( [] )
    for step in RLEseq:
        RLEusedChans |= set(step[1]) #make a set with all of the swab channels that get used

    swabSeq = Sequence()
    for chan in RLEusedChans:
        chanPulsePattern = [ (step[0], int(chan in step[1]) ) for step in RLEseq] #loop over steps, have (dur, 1) if chan is on in step, else (dur 0)
        swabSeq.setDigital(chan, chanPulsePattern)

    return(swabSeq)


def convertRLEtoSeq(RLEseq):
    '''Converts sequences of the form [ (Duration in ns, [Dig Chans to Turn On], A0, A1), (Dur in ns, [Dig Chans On], A0, A1), ...]
    type sequences to Swabian Sequences (mostly to aid with plotting)'''
    RLEusedChans = set( [] )
    for step in RLEseq:
        RLEusedChans |= set(step[1]) #make a set with all of the swab channels that get used

    swabSeq = Sequence()
    for chan in RLEusedChans:
        chanPulsePattern = [ (step[0], int(chan in step[1]) ) for step in RLEseq] #loop over steps, have (dur, 1) if chan is on in step, else (dur 0)
        swabSeq.setDigital(chan, chanPulsePattern)
    swabSeq.setAnalog(0, [(step[0], step[2]) for step in RLEseq]) 
    swabSeq.setAnalog(1, [(step[0], step[3]) for step in RLEseq]) 

    return(swabSeq)


def convertSecArgsToNanosec(*args):
    '''Converts a handful of args in seconds to an appropriate number of integer nanoseconds to be Swabian-compatible'''
    return [int(val*1e9) for val in args]

def convertSecKwargsToNanosec(**kwargs):
    '''Converts a handful of kwargs in seconds to an appropriate number of integer nanoseconds to be Swabian-compatible'''
    return dict([key, int(val*1e9)] for key,val in kwargs.items())



class Pulses():
    '''Class containing pulse sequences to run many common NV experiments on Blissey using tree-free DAQ counting. Reads will always start
    with a high flag during the first "dead time" window, and reads will be between two 25ns (by default) rising edges on the CLK channel'''
    #0 connected to AOM, 4 connected to Vaunix switch, Clk/D4 and Trig/D6 are connected to PFI0,PFI5 respectively. 
    DIG_CHAN_DICT = {'aomSwitch': 'AO', 'rfSwitch': 7, 'Clk': 4, 'Trig': 6} 
    
    DEFAULT_TIME_UNIT = 'ns'
    FAULT_V_UNIT = 'V'
    DEFAULT_CLK_PULSE_DUR = 25 #ns
    DEFAULT_AOM_VOLTAGE = 0.9 #V

    #General sequence is of the form:
    #[(duration in ns, [list of channels to turn on, others are off (empty is all off)], A0_Voltage, A1_Voltage), (duration2, [channel2], A0V_2, A1V_2), ...]
    def __init__(self):
        pass


    def rawMwPulse(self, mwTime:int):
        '''Returns a Swabian Seq-compatible list that will switch MWs on for mwTime
        Arguments:  *mwTime, time to turn MWs on for (in ns)'''
        return( [(mwTime, [self.DIG_CHAN_DICT['rfSwitch']], 0,0)] )


    def rawLaserPulse(self, laserTime:int, aomV=DEFAULT_AOM_VOLTAGE):
        '''Returns a Swabian Seq-compatible list that will switch laser on for laserTime
        Arguments:  *laserTime, time to turn laser on for (in ns)
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)'''
        return( [(laserTime, [], aomV,0)] )


    def wait(self, delayTime:int):
        '''Returns a Swabian Seq-compatible list with all channels off for delayTime
        Arguments:  *delayTime, time to do nothing (in ns)'''
        return( [(delayTime, [], 0,0)] )
    

    def comboPulse(self, time:int, aomV=DEFAULT_AOM_VOLTAGE):
        '''Returns a Swabian Seq-compatible list that will switch laser and MWs on for mwTime (naively, ignores AOM lag)
        Arguments:  *mwTime, time to turn MWs on for (in ns)
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)'''
        return( [(time, [self.DIG_CHAN_DICT['rfSwitch']], aomV,0)])
    

    def rawReadOutPulse(self, readOutTime:int, aomV=DEFAULT_AOM_VOLTAGE):
        '''Returns a Swabian Seq-compatible list with laser on and specified counter channel on for readOutTime
        Arguments:  *readOutTime, time to have laser on and counter channel open for (in ns)
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)'''
        if readOutTime <= self.DEFAULT_CLK_PULSE_DUR:
            raise(ValueError(f'Specified Readout Time {readOutTime} is less than the {self.DEFAULT_CLK_PULSE_DUR}ns length of a CLK pulse'))
        
        return( [(self.DEFAULT_CLK_PULSE_DUR, [self.DIG_CHAN_DICT['Clk']], aomV,0),
                 (readOutTime-self.DEFAULT_CLK_PULSE_DUR, [], aomV,0),
                 (self.DEFAULT_CLK_PULSE_DUR, [self.DIG_CHAN_DICT['Clk']], aomV,0)] )


    def rawReadoutAndInitPulse(self, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, aomV=DEFAULT_AOM_VOLTAGE):
        '''Returns a Swabian Seq-compatible list with a readout pulse with specified counterChan
        for readOutTime, then just laser on for extraInitLaserTime before waiting for aomFallLagAndISC time with everything off
        NOTE: Differs from readoutAndInitPulse by NOT pre-buffering an AOM rise
        Arguments:  *readOutTime, time to have laser on and counter channel open for (in ns)
                    *extraInitLaserTime, time to have laser on to reset NV state (in ns)
                    *aomFallLagAndISC, time to wait for AOM to fall and for ISC to depopulate (in ns)
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)'''

        readOutWindow = self.rawReadOutPulse(readOutTime, aomV)
        extraLaserForInit = self.rawLaserPulse(extraInitLaserTime, aomV)
        aomLagAndIscDelay = self.wait(aomFallLagAndISC)
        return(readOutWindow + extraLaserForInit + aomLagAndIscDelay)
    
    
    def readoutAndInitPulse(self, aomRiseLag:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, aomV=DEFAULT_AOM_VOLTAGE, flag=False):
        '''Returns a Swabian Seq-compatible list with laser on for an aomRiseLag time, then a readout pulse with specified counterChan
        for readOutTime, then just laser on for extraInitLaserTime before waiting for aomFallLagAndISC time with everything off
        Arguments:  *readOutTime, time to have laser on and counter channel open for (in ns)
                    *extraInitLaserTime, time to have laser on to reset NV state (in ns)
                    *aomRiseLag, time to have laser on before counting corresponding to how long the AOM takes to rise (in ns)
                    *aomFallLagAndISC, time to wait for AOM to fall and for ISC to depopulate (in ns)
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)
                    *flag (default False): whether to turn on the flag channel for the length of a Clk pulse when the AOM buffering starts'''
        if flag:
            if aomRiseLag <= self.DEFAULT_CLK_PULSE_DUR:
                raise(ValueError(f'Specified AOM Rise {aomRiseLag}ns is less than the {self.DEFAULT_CLK_PULSE_DUR}ns length of a CLK pulse. Cant send FLAG pulse during AOM buffer'))
            aomLagCompensation = [(self.DEFAULT_CLK_PULSE_DUR, [self.DIG_CHAN_DICT['Trig']], aomV,0)] + self.rawLaserPulse(aomRiseLag-self.DEFAULT_CLK_PULSE_DUR, aomV)
        else:
            aomLagCompensation = self.rawLaserPulse(aomRiseLag, aomV)

        rawReadoutAndInitPulse = self.rawReadoutAndInitPulse(readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV)
        return(aomLagCompensation + rawReadoutAndInitPulse)


    def readOutWithMWs(self, preReadoutLaserAndMwTime:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, aomV=DEFAULT_AOM_VOLTAGE, flag=False):
        '''Returns a Swabian Seq-compatible list with laser+MWs on for an preReadoutLaserAndMwTime, then a readout pulse with specified counterChan
        for readOutTime with laser+MWs, then just laser on for extraInitLaserTime before waiting for aomFallLagAndISC time with everything off
        Arguments:  *preReadoutLaserAndMwTime, time to have laser+MWs on before counting (should at least be long enough for AOM to rise) (in ns)
                    *readOutTime, time to have laser+MWs on and counter channel open for (in ns)
                    *extraInitLaserTime, time to have only laser on to reset NV state (in ns)
                    *aomFallLagAndISC, time to wait for AOM to fall and for ISC to depopulate (extra delay can be added here) (in ns)
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)
                    *flag (default False): whether to turn on the flag channel for the length of a Clk pulse when the AOM buffering starts'''
        if readOutTime <= self.DEFAULT_CLK_PULSE_DUR:
            raise(ValueError(f'Specified Readout Time {readOutTime} is less than the {self.DEFAULT_CLK_PULSE_DUR}ns length of a CLK pulse'))
        
        if flag:
            if preReadoutLaserAndMwTime <= self.DEFAULT_CLK_PULSE_DUR:
                raise(ValueError(f'Specified preRO Laser+MW time {preReadoutLaserAndMwTime}ns is less than the {self.DEFAULT_CLK_PULSE_DUR}ns length of a CLK pulse. Cant send FLAG pulse during AOM buffer'))
            preReadoutLaserAndMws = [(self.DEFAULT_CLK_PULSE_DUR, [self.DIG_CHAN_DICT['Trig'], self.DIG_CHAN_DICT['rfSwitch']], aomV,0)] + [(preReadoutLaserAndMwTime-self.DEFAULT_CLK_PULSE_DUR, [self.DIG_CHAN_DICT['rfSwitch']], aomV,0)]
        else:
            preReadoutLaserAndMws = [(preReadoutLaserAndMwTime, [self.DIG_CHAN_DICT['rfSwitch']], aomV,0)]
        
        readOutWindow = [(self.DEFAULT_CLK_PULSE_DUR, [self.DIG_CHAN_DICT['rfSwitch'],self.DIG_CHAN_DICT['Clk']], aomV,0),
                         (readOutTime-self.DEFAULT_CLK_PULSE_DUR, [self.DIG_CHAN_DICT['rfSwitch']], aomV,0),
                         (self.DEFAULT_CLK_PULSE_DUR, [self.DIG_CHAN_DICT['rfSwitch'],self.DIG_CHAN_DICT['Clk']], aomV,0)]
        extraLaserForInit = self.rawLaserPulse(extraInitLaserTime, aomV)
        aomLagAndIscDelay = self.wait(aomFallLagAndISC)
        return(preReadoutLaserAndMws + readOutWindow + extraLaserForInit + aomLagAndIscDelay)


    #now for the actual measurement sequences
    def cwODMRwithBackground(self, preReadoutLaserAndMwTime:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, aomV=DEFAULT_AOM_VOLTAGE):
        '''Returns a Swabian Seq-compatible list with laser+MWs (no counting) for a preReadout time, then reads out with CW laser+MWs to Chan1
        before running just the laser to re-init the NV state to 0 before waiting some time with everything off for the AOM to fall and ISC to depopulate
        for readOutTime with laser+MWs, then just laser on for extraInitLaserTime before waiting for aomFallLagAndISC time with everything off.
        This sequence with idential timings is repeated with no MWs and counts going into Chan2
        Arguments:  *preReadoutLaserAndMwTime, time to have laser+MWs on before counting (should at least be long enough for AOM to rise) (in ns)
                    *readOutTime, time to have laser+MWs on and counter channel open for (in ns)
                    *extraInitLaserTime, time to have only laser on to reset NV state (in ns)
                    *aomFallLagAndISC, time to wait for AOM to fall and for ISC to depopulate (extra delay can be added here) (in ns)
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)'''
        withMwsSeq = self.readOutWithMWs(preReadoutLaserAndMwTime, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV, flag=True)
        withoutMwsSeq = self.readoutAndInitPulse(preReadoutLaserAndMwTime, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV)
        return(withMwsSeq + withoutMwsSeq)
    

    #old 'inefficient' pulse sequences that take background everywhere
    def rabiWithBackground(self, tauTime:int, maxTauTime:int, aomRiseLagTime:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, bufferTime:int=0, aomV=DEFAULT_AOM_VOLTAGE): #TODO: Rename this since it's not balanced, it just does background counting
        '''Returns a Rabi pulse sequence with balanced duty cycle which turns a laser on for aomRiseLag before opening a counter channel and collecting counts for readoutTime
        and reinit-ing the NV for extraInitLaserTime before waiting for aomFallLagAndISC and maxTauTime-tauTime (to balance duty cycle) before applying MWs for tauTime, waiting for an optional buffer time,
        and then repeating the same sequence but without applying any microwaves (readouts are into countChans 1 and 2, respectively)
        Arguments:  *tauTime, time to apply MWs for this Rabi experiment
                    *maxTauTime, max time for Rabi sweep, used to normalize duty cycles
                    *aomRiseLag, time to buffer AOM rise before a laser pulse
                    *readOutTime, time to have ctr channel open for 
                    *extraInitLaserTime, time to leave laser on to reinit NV
                    *aomFallLagAndISC, time to wait for lasser off + ISC to depopulate (recall, still waiting for maxTau-tauTime after this before MW pulse)
                    *bufferTime, time to wait between MW pulse and start of (AOM buffering for) readout. Default is 0
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)
        '''
        mwSeq = self.readoutAndInitPulse(aomRiseLagTime, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV, flag=True ) + self.wait(maxTauTime-tauTime) + self.rawMwPulse(tauTime)
        noMwSeq = self.readoutAndInitPulse(aomRiseLagTime, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV ) + self.wait(maxTauTime-tauTime) + self.wait(tauTime)
        if bufferTime != 0:
            return(mwSeq + self.wait(bufferTime) + noMwSeq + self.wait(bufferTime))
        else:
            return(mwSeq + noMwSeq)
        

    def pODMRwithBackground(self, piPulseTime:int, aomRiseLagTime:int, readOutTime:int, initTime:int, aomFallLagAndISC:int, bufferTime:int=0, aomV=DEFAULT_AOM_VOLTAGE):
        '''Returns a Swabian compatible sequence for pulsed ODMR or, as I call it, 'pod-mer' 
        Arguments:  *aomRiseLagTime, time(ns) for AOM to turn on before measurement
                    *readOutTime, time(ns) for laser to be on and for counter channel to be open
                    *initTime, time(ns) with only laser on to reset NV state
                    *aomFallLagAndISC, time(ns) where everything is off to account for AOM turning off and ISC before the MW pulse
                    *piPulseTime, time(ns) the MW is on
                    *bufferTime=0, time(ns) after pi pulse before (AOM start buffering for) readout
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)
        '''
        seqWithMws = self.readoutAndInitPulse(aomRiseLagTime, readOutTime, initTime,  aomFallLagAndISC, aomV, flag=True) + self.rawMwPulse(piPulseTime) + self.wait(bufferTime) 
        seqNoMWs =  self.readoutAndInitPulse(aomRiseLagTime, readOutTime, initTime,  aomFallLagAndISC, aomV) + self.wait(piPulseTime) + self.wait(bufferTime)
        return(seqWithMws + seqNoMWs)
    

    def tripleRamsey(self, halfPiTime:int, threeHalfPiTime:int, tauTime:int, maxTauTime:int, aomRiseLag:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, bufferTime:int=0, aomV=DEFAULT_AOM_VOLTAGE):
        '''Returns a Ramsey pulse sequence with balanced duty cycle which turns a laser on for aomRiseLag before opening a counter channel and collecting counts for readoutTime
        and reinit-ing the NV for extraInitLaserTime before waiting for aomFallLagAndISC and maxTauTime-tauTime (to balance duty cycle) before applying a Pi/2 pulse, waiting for tauTime,
        applying another Pi/2 pulse, and finally waiting for an optional buffer time. Then repeats same seq but with the 2nd MW pulse being a 3pi/2 pulse, and then with both pi/2 pulses replaced with waits
        Arguments:  *halfPiTime, time needed to drive a pi/2 pulse
                    *halfPiTime, time needed to drive a 3pi/2 pulse
                    *tauTime, time to apply wait between pi/2 (or pi/2, 3pi/2) pulses
                    *maxTauTime, max time for Ramsey sweep, used to normalize duty cycles
                    *aomRiseLag, time to buffer AOM rise before a laser pulse
                    *readOutTime, time to have ctr channel open for 
                    *extraInitLaserTime, time to leave laser on to reinit NV
                    *aomFallLagAndISC, time to wait for lasser off + ISC to depopulate (recall, still waiting for maxTau-tauTime after this before MW pulse)
                    *bufferTime, time to wait between MW pulse and start of (AOM buffering for) readout. Default is 0
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)
        '''
        pi2pi2Seq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV, flag=True) + self.wait(maxTauTime-tauTime) + self.rawMwPulse(halfPiTime)+ self.wait(tauTime) + self.rawMwPulse(halfPiTime)
        pi2pi32Seq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV) + self.wait(maxTauTime-tauTime) + self.rawMwPulse(halfPiTime)+ self.wait(tauTime) + self.rawMwPulse(threeHalfPiTime)
        noMwSeq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV) + self.wait(maxTauTime-tauTime) + self.wait(halfPiTime) + self.wait(tauTime) + self.wait(halfPiTime)
        return(pi2pi2Seq + self.wait(bufferTime) + pi2pi32Seq + self.wait(bufferTime) + noMwSeq + self.wait(bufferTime))
    

    def balancedDiffT2Hahn(self, halfPiPulseTime:int, piPulseTime:int, threeHalvesPiPulseTime:int, shortTauTimeOverTwo:int, longTauTimeOverTwo:int, aomRiseLag:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, bufferTime:int=0, aomV:float=DEFAULT_AOM_VOLTAGE):
        '''Returns a balanced differential T2 pulse sequence by running a T2 sequence with waits of shortTauTimeOverTwo between the pi/2-pi-pi/2 pulses
        followed by a similar sequence with waits longTauTimeOverTwo that ends up with a 3pi/2-pulse
        Arguments:  *halfPiPulseTime, time needed to drive a pi/2 pulse
                    *piPulseTime, time needed to drive a pi-pulse
                    *threeHalvesPiPulseTime, time needed to drive a 3pi/2 pulse
                    *shortTauTimeOverTwo, time to wait between the pi/2-pi-pi/2 pulses (not necessarily shorter than longTauTime)
                    *longTauTimeOverTwo, time to wait between the pi/2-pi-3pi/2 pulses (not necessarily longer than shortTauTime)
                    *aomRiseLag, time to buffer AOM rise before a laser pulse
                    *readOutTime, time to have ctr channel open for 
                    *extraInitLaserTime, time to leave laser on to reinit NV
                    *aomFallLagAndISC, time to wait for lasser off + ISC to depopulate (recall, still waiting for maxTau-tauTime after this before MW pulse)
                    *bufferTime, time to wait between MW pulse and start of (AOM buffering for) readout. Default is 0
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)
        '''
        shortTwoHalfPulseSeq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV, flag=True) + self.rawMwPulse(halfPiPulseTime) + self.wait(shortTauTimeOverTwo) + self.rawMwPulse(piPulseTime) + self.wait(shortTauTimeOverTwo) + self.rawMwPulse(halfPiPulseTime)
        longHalfThreeHalfPulseSeq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV) + self.rawMwPulse(halfPiPulseTime) + self.wait(longTauTimeOverTwo) + self.rawMwPulse(piPulseTime) + self.wait(longTauTimeOverTwo) + self.rawMwPulse(threeHalvesPiPulseTime)
        if bufferTime != 0:
            return(shortTwoHalfPulseSeq + self.wait(bufferTime) + longHalfThreeHalfPulseSeq +self.wait(bufferTime) )
        else:
            return(shortTwoHalfPulseSeq + longHalfThreeHalfPulseSeq )
        
    
    def balancedDiffT1(self, piPulseTime:int, shortTauTime:int, longTauTime:int, aomRiseLag:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, bufferTime:int=0, aomV:float=DEFAULT_AOM_VOLTAGE):
        '''Returns a balanced differential T1 pulse sequence by running a no-MW T1 sequence for shortTau (aomRiseLag, readoutPulse, extraInitLaserTime,
        aomFallLag and ISC wait) followed by a similar sequence for longTau that ends up with a pi-pulse and optional wait for bufferTime before repeating.
        Arguments:  *piPulseTime, time needed to drive a pi-pulse
                    *shortTauTime, time to wait after init before readout (not necessarily shorter than longTauTime)
                    *longTauTime, time to wait after init before pi-pulse and readout (not necessarily longer than shortTauTime)
                    *aomRiseLag, time to buffer AOM rise before a laser pulse
                    *readOutTime, time to have ctr channel open for 
                    *extraInitLaserTime, time to leave laser on to reinit NV
                    *aomFallLagAndISC, time to wait for lasser off + ISC to depopulate (recall, still waiting for maxTau-tauTime after this before MW pulse)
                    *bufferTime, time to wait between MW pulse and start of (AOM buffering for) readout. Default is 0
                    *aomV (default DEFAULT_AOM_VOLTAGE), voltage to turn AOM on with (in V)
        '''
        noPulseSeq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV, flag=True) + self.wait(shortTauTime)
        piPulseSeq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, aomV) + self.wait(longTauTime) + self.rawMwPulse(piPulseTime)
        if bufferTime != 0:
            return(noPulseSeq + piPulseSeq + self.wait(bufferTime))
        else:
            return(noPulseSeq + piPulseSeq)
    


    #purely experimental calibration sequences
    def aomPlusSwitchDelayCal(self, laserStartTime:int, laserDur:int, countStartTime:int, countDur:int, fullLengthWithBuffer:int, clkPulseDur:int=DEFAULT_CLK_PULSE_DUR, ifFlag:bool=False, aomV:float=DEFAULT_AOM_VOLTAGE):
        '''Returns a Swabian Seq(!) with the AOM turned on at a specified laserStartTime for laserDur, as well as a specified counter opened
        at specified countStartTime for a countDur, then the seq repeats every fullLengthWithBuffer (which must be a multiple of 8ns for the Swab to loop it optimally)
        Arguments:  *laserStartTime, time to turn on the laser (in ns)
                    *laserDur, how long to turn the laser on for (in ns)
                    *countStartTime, time to turn on the desired counting channel (in ns)
                    *countDur, how long to turn the counting channel on for (in ns)
                    *fullLengthWithBuffer, total time of sequence (in ns), preferably a multiple of 8ns 
                    *clkPulseDur, duration of a clk pulse (should at least 8ns), default DEFAULT_CLK_PULSE_DUR=50ns
                    *ifFlag, bool if flag channel should be used, default False
                    *aomV, voltage to be used to set AOM on, default DEFAULT_AOM_VOLTAGE=0.9'''
        if countDur <= 2*clkPulseDur:
            raise(ValueError(f'Count Duration {countDur}ns is less than Length of 2 {clkPulseDur}ns Clock Pulses'))
        if ifFlag and countStartTime <= 2*clkPulseDur:
            raise(ValueError(f'Count Start Time {countStartTime}ns is less than Length of 2 {clkPulseDur}ns Clock Pulses'))
        seq = Sequence() 
        seq.setAnalog(0, [(laserStartTime, 0), (laserDur, aomV), (fullLengthWithBuffer-(laserStartTime+laserDur), 0)] ) #switch the laser on only for the laserDur
        seq.setDigital(self.DIG_CHAN_DICT['Clk'], [(countStartTime, 0), (clkPulseDur, 1), (countDur-clkPulseDur, 0),  (clkPulseDur, 1), (clkPulseDur, 0), (fullLengthWithBuffer-(countStartTime+countDur+2*clkPulseDur), 0)] )
        if ifFlag:
            seq.setDigital(self.DIG_CHAN_DICT['Trig'], [(clkPulseDur, 1), (clkPulseDur, 0), (fullLengthWithBuffer-2*clkPulseDur, 0)] )
        return(seq, seq.getDuration())#.getData())

    #Pausing these for now until I figure out what to do about flagging
    """
    


    def ramsey(self, halfPiTime:int, tauTime:int, maxTauTime:int, aomRiseLag:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, bufferTime:int=0):
        '''Returns a basic Ramsey pulse sequence with balanced duty cycle which turns a laser on for aomRiseLag before opening a counter channel and collecting counts for readoutTime
        and reinit-ing the NV for extraInitLaserTime before waiting for aomFallLagAndISC and maxTauTime-tauTime (to balance duty cycle) before applying a Pi/2 pulse, waiting for tauTime,
        applying another pi/2 pulse, anf finally waiting for an optional buffer time
        Arguments:  *halfPiTime, time needed to drive a pi/2 pulse
                    *tauTime, time to apply wait between pi/2 pulses
                    *maxTauTime, max time for Ramsey sweep, used to normalize duty cycles
                    *aomRiseLag, time to buffer AOM rise before a laser pulse
                    *readOutTime, time to have ctr channel open for 
                    *extraInitLaserTime, time to leave laser on to reinit NV
                    *aomFallLagAndISC, time to wait for lasser off + ISC to depopulate (recall, still waiting for maxTau-tauTime after this before MW pulse)
                    *bufferTime, time to wait between MW pulse and start of (AOM buffering for) readout. Default is 0
        '''
        seq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, countChan=1) + self.wait(maxTauTime-tauTime) + self.rawMwPulse(halfPiTime)+ self.wait(tauTime) + self.rawMwPulse(halfPiTime)
        return(seq)
    

    def ramseyWithBackground(self, halfPiTime:int, tauTime:int, maxTauTime:int, aomRiseLag:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, bufferTime:int=0):
        '''Returns a basic Ramsey pulse sequence with balanced duty cycle which turns a laser on for aomRiseLag before opening a counter channel and collecting counts for readoutTime
        and reinit-ing the NV for extraInitLaserTime before waiting for aomFallLagAndISC and maxTauTime-tauTime (to balance duty cycle) before applying a Pi/2 pulse, waiting for tauTime,
        applying another pi/2 pulse, anf finally waiting for an optional buffer time. Repeats same seq but with delays instead of the pi/2 pulses.
        Arguments:  *halfPiTime, time needed to drive a pi/2 pulse
                    *tauTime, time to apply wait between pi/2 pulses
                    *maxTauTime, max time for Ramsey sweep, used to normalize duty cycles
                    *aomRiseLag, time to buffer AOM rise before a laser pulse
                    *readOutTime, time to have ctr channel open for 
                    *extraInitLaserTime, time to leave laser on to reinit NV
                    *aomFallLagAndISC, time to wait for lasser off + ISC to depopulate (recall, still waiting for maxTau-tauTime after this before MW pulse)
                    *bufferTime, time to wait between MW pulse and start of (AOM buffering for) readout. Default is 0
        '''
        mwSeq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, countChan=1) + self.wait(maxTauTime-tauTime) + self.rawMwPulse(halfPiTime)+ self.wait(tauTime) + self.rawMwPulse(halfPiTime)
        noMwSeq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime, aomFallLagAndISC, countChan=2) + self.wait(maxTauTime-tauTime) + self.wait(halfPiTime)+ self.wait(tauTime) + self.wait(halfPiTime)
        return(mwSeq+noMwSeq)
    

   
    """

    #from when I thought reading out as soon as the MWs stopped was the most important thing. It it not. -CE
    """    
    def _bufferMwSeqWithAomRise(self, swabMwSeq, aomRiseTime, lastPulseToRoBuffer=0):
        '''Returns a Swabian sequence based
        Built to R/O right after 2nd MW pulse, so the AOM will be pre-cooked to turn on right (or after a short buffer time) after 2nd MW pulse ends
        Also, will buffer duty cycle with init laser (should be fine... right) #TODO: Make sure this is right
        Arguments:  *readOutTime, time(ns) for laser to be on and for counter channel(s) to be open
                    *initTime, time(ns) with only laser on to reset NV state
                    *aomRiseTime, time(ns) for only AOM lag where everything is off. this should NOT include ISC or other delays
                    *iscWaitTime, time(ns) where everything is off to account for ISC
                    *tau, time(ns) after to wait between first and second MW pulses
                    *maxTau, max time(ns) between first and second MW pulses to balance duty cycles (with init laser)
                    *halfPiPulseTime, time(ns) needed for MWs to drive pi/2 transition
                    *threeHalvesPiPulseTime, time(ns) needed for MWs to drive 3/2pi transition
                    *secondPulseToRObuffer, time(ns) of a buffer between the 2nd MW pulse and the start of the R/O window
        '''
        
        twoHalfPulsesSeq = Sequence() #easier to do things with swab seqs
        twoHalfPulsesSeq.setDigital(self.DIG_CHAN_DICT['rfSwitch'], [(halfPiPulseTime, 1), (tau, 0), (halfPiPulseTime, 1), (1, 0)]) #apply MW pulses, padding with 1ns of 0, otherwise extending this seq keeps MWs on
        if aomRiseTime-secondPulseToRObuffer <= twoHalfPulsesSeq.getDuration(): #if that pulse seq takes longer than the AOM buffer, just start buffering the AOM in the middle
            twoHalfPulsesSeq.setDigital(self.DIG_CHAN_DICT['aomSwitch'], [(twoHalfPulsesSeq.getDuration()-(aomRiseTime-secondPulseToRObuffer), 0), ((aomRiseTime-secondPulseToRObuffer), 1)])
        else: #if the AOM needs more buffer than the length of the seq, then turn the laser on for a bit beforehand and then for the whole MW pulse seq
            twoHalfPulsesSeq.setDigital(self.DIG_CHAN_DICT['aomSwitch'], [(twoHalfPulsesSeq.getDuration(),1)])
            twoHalfPulsesSeq = convertDigRLEtoSeq( [ [(aomRiseTime-secondPulseToRObuffer)-twoHalfPulsesSeq.getDuration(), [self.DIG_CHAN_DICT['aomSwitch']]], ] ) + twoHalfPulsesSeq):

        pass
    """
    """def diffRamsey(self, readOutTime, initTime, aomRiseTime, aomFallLagTime, iscWaitTime, tau, maxTau, halfPiPulseTime, threeHalvesPiPulseTime, secondPulseToRObuffer=0):
        '''Returns a Swabian compatible sequence for a differential Ramsey measurement 
        Built to R/O right after 2nd MW pulse, so the AOM will be pre-cooked to turn on right (or after a short buffer time) after 2nd MW pulse ends
        Also, will buffer duty cycle with init laser (should be fine... right) #TODO: Make sure this is right
        Arguments:  *readOutTime, time(ns) for laser to be on and for counter channel(s) to be open
                    *initTime, time(ns) with only laser on to reset NV state
                    *aomRiseTime, time(ns) for only AOM lag where everything is off. this should NOT include ISC or other delays
                    *iscWaitTime, time(ns) where everything is off to account for ISC
                    *tau, time(ns) after to wait between first and second MW pulses
                    *maxTau, max time(ns) between first and second MW pulses to balance duty cycles (with init laser)
                    *halfPiPulseTime, time(ns) needed for MWs to drive pi/2 transition
                    *threeHalvesPiPulseTime, time(ns) needed for MWs to drive 3/2pi transition
                    *secondPulseToRObuffer, time(ns) of a buffer between the 2nd MW pulse and the start of the R/O window
        '''
        
        twoHalfPulsesSeq = Sequence() #easier to do things with swab seqs
        twoHalfPulsesSeq.setDigital(self.DIG_CHAN_DICT['rfSwitch'], [(halfPiPulseTime, 1), (tau, 0), (halfPiPulseTime, 1), (1, 0)]) #apply MW pulses, padding with 1ns of 0, otherwise extending this seq keeps MWs on
        if aomRiseTime-secondPulseToRObuffer <= twoHalfPulsesSeq.getDuration(): #if that pulse seq takes longer than the AOM buffer, just start buffering the AOM in the middle
            twoHalfPulsesSeq.setDigital(self.DIG_CHAN_DICT['aomSwitch'], [(twoHalfPulsesSeq.getDuration()-(aomRiseTime-secondPulseToRObuffer), 0), ((aomRiseTime-secondPulseToRObuffer), 1)])
        else: #if the AOM needs more buffer than the length of the seq, then turn the laser on for a bit beforehand and then for the whole MW pulse seq
            twoHalfPulsesSeq.setDigital(self.DIG_CHAN_DICT['aomSwitch'], [(twoHalfPulsesSeq.getDuration(),1)])
            twoHalfPulsesSeq = convertDigRLEtoSeq( [ [(aomRiseTime-secondPulseToRObuffer)-twoHalfPulsesSeq.getDuration(), [self.DIG_CHAN_DICT['aomSwitch']]], ] ) + twoHalfPulsesSeq

        halfThen3HalfPulsesSeq = Sequence() #now do the same thing with a 3pi/2 for the 2nd MW pulse
        halfThen3HalfPulsesSeq.setDigital(self.DIG_CHAN_DICT['rfSwitch'], [(halfPiPulseTime, 1), (tau, 0), (threeHalvesPiPulseTime, 1), (1, 0)]) #apply MW pulses,  padding with 1ns of 0, otherwise extending this seq keeps MWs on
        if aomRiseTime-secondPulseToRObuffer <= halfThen3HalfPulsesSeq.getDuration(): #if that pulse seq takes longer than the AOM buffer, just start buffering the AOM in the middle
            halfThen3HalfPulsesSeq.setDigital(self.DIG_CHAN_DICT['aomSwitch'], [(halfThen3HalfPulsesSeq.getDuration()-(aomRiseTime-secondPulseToRObuffer), 0), ((aomRiseTime-secondPulseToRObuffer), 1)])
        else: #if the AOM needs more buffer than the length of the seq, then turn the laser on for a bit beforehand and then for the whole MW pulse seq
            halfThen3HalfPulsesSeq.setDigital(self.DIG_CHAN_DICT['aomSwitch'], [(halfThen3HalfPulsesSeq.getDuration(),1)])
            halfThen3HalfPulsesSeq = convertDigRLEtoSeq( [ [(aomRiseTime-secondPulseToRObuffer)-halfThen3HalfPulsesSeq.getDuration(), [self.DIG_CHAN_DICT['aomSwitch']]], ] ) + halfThen3HalfPulsesSeq
        
        maxDcBalanceTime = max(aomRiseTime, maxTau+halfPiPulseTime+threeHalvesPiPulseTime)
        roInto1ReinitAomFallAndIsc = self.rawReadoutAndInitPulse(readOutTime, initTime+(maxDcBalanceTime - twoHalfPulsesSeq.getDuration()), aomFallLagTime+iscWaitTime, countChan=1)
        roInto2ReinitAomFallAndIsc = self.rawReadoutAndInitPulse(readOutTime, initTime+(maxDcBalanceTime - halfThen3HalfPulsesSeq.getDuration()), aomFallLagTime+iscWaitTime, countChan=2)

        roInto1ReinitAomFallAndIsc = convertDigRLEtoSeq(roInto1ReinitAomFallAndIsc)
        roInto2ReinitAomFallAndIsc = convertDigRLEtoSeq(roInto2ReinitAomFallAndIsc)

        if secondPulseToRObuffer:
            buffer = convertDigRLEtoSeq(self.wait(secondPulseToRObuffer))
            seq = twoHalfPulsesSeq + buffer + roInto1ReinitAomFallAndIsc + halfThen3HalfPulsesSeq + buffer + roInto2ReinitAomFallAndIsc
        else:
            seq = twoHalfPulsesSeq + roInto1ReinitAomFallAndIsc + halfThen3HalfPulsesSeq + roInto2ReinitAomFallAndIsc
        
        return(seq)
    """

    #ALSO BLOCKING THESE OUT UNTIL I FIGURE OUT FLAGGING
    """def diffT1(self, piPulseTime:int, tauTime:int, maxTauTime:int, aomRiseLag:int, readOutTime:int, extraInitLaserTime:int, aomFallLagAndISC:int, bufferTime:int=0):
        '''Returns a differential T1 pulse sequence with fixed duty cycle (by padding the reinit time) which turns a laser on for aomRiseLag before opening a counter channel and collecting counts for readoutTime
        and reinit-ing the NV for extraInitLaserTime+maxTau-tauTime (to balance duty cycles) before waiting for aomFallLagAndISC and tauTime. This then repeats but with a Pi-pulse
        at the end (followed by an optional buffer time before readout).
        Arguments:  *piPulseTime, time needed to drive a pi-pulse
                    *tauTime, time to wait after init and readout (or pi-pulse before readout)
                    *maxTauTime, max wait time of sweep, used to normalize duty cycles
                    *aomRiseLag, time to buffer AOM rise before a laser pulse
                    *readOutTime, time to have ctr channel open for 
                    *extraInitLaserTime, time to leave laser on to reinit NV
                    *aomFallLagAndISC, time to wait for lasser off + ISC to depopulate (recall, still waiting for maxTau-tauTime after this before MW pulse)
                    *bufferTime, time to wait between MW pulse and start of (AOM buffering for) readout. Default is 0
        '''
        noPulseSeq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime+(maxTauTime-tauTime), aomFallLagAndISC, countChan=1) + self.wait(tauTime)
        piPulseSeq = self.readoutAndInitPulse(aomRiseLag, readOutTime, extraInitLaserTime+(maxTauTime-tauTime), aomFallLagAndISC, countChan=2) + self.wait(tauTime) + self.rawMwPulse(piPulseTime)
        if bufferTime != 0:
            return(noPulseSeq + piPulseSeq + self.wait(bufferTime))
        else:
            return(noPulseSeq + piPulseSeq)


    '''def diffT2Hahn(self, piPulseTime, halfPiPulseTime, tauTime, readOutTime, initTime, aomRiseLagTime, aomFallLagTime, iscLagTime):

        piPulse = self.rawMwPulse(piPulseTime)
        halfPiPulse = self.rawMwPulse(halfPiPulseTime)
        tau = self.wait(tauTime)

        bgPi = self.wait(piPulseTime)
        bgHalfPi = self.wait(halfPiPulseTime)

        buffer = self.wait(maxTauTime-tauTime)

        roI = self.readoutAndInitPulse(aomRiseLagTime, readOutTime, initTime, aomFallLagTime+iscLagTime, countChan=1)
        bg = self.readoutAndInitPulse(aomRiseLagTime, readOutTime, initTime, aomFallLagTime+iscLagTime, countChan=2)

        return(halfPiPulse + tau + piPulse + tau + halfPiPulse + roI + bgHalfPi + tau + bgPi + tau + bgHalfPi + bg )'''
    

    """

#fix message at the top when you're done