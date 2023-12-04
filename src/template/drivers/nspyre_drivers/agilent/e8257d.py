
import string
import numpy as np
import pyvisa
from pyvisa import ResourceManager

"""

Some notes: 0 = False, and 1 = True for most of the get functions that refer to on or off

When using these functions in experiments, make sure to call the function as the following:
Say you wanted to use idn(), you would use it by doing something like this in your experimental file,

from [this file path] import AgilentE8257D as AGD

idn(AGD)

I know, weird, but this was the only way to get it to work as of 10/27/2023. 'self' needs to be the class, so 'AGD'

"""

class AgilentE8257D:
        
    DEFAULTS = {
        'COMMON': {
            'write_termination': '\n',
            'read_termination': '\n',
        }
    }
    
    rm = pyvisa.ResourceManager()
    address='192.168.1.45'

    def SG_Connect():
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        print(f"List of connected instruments: {resources}")
        SG=rm.open_resource(resources[1])
        print(f"Using the following instrument: {SG.query('*IDN?')}")
        return SG
    
    def idn(self):
        SG = self.SG_Connect()
        return SG.query('*IDN?')

    
    def get_lf_amplitude(self):
        """
        low frequency ampitude (BNC output)
        """
        SG = self.SG_Connect()
        LF_amp = float(SG.query('LFO:AMPL?'))
        return LF_amp
    
    
    def set_lf_amplitude(self,value):
        SG = self.SG_Connect()
        SG.write('LFO:AMPL {:.2f}'.format(value))
        
    
    def get_rf_amplitude(self):
        """
        RF amplitude (Type N output)
        units are in dBm
        """
        SG = self.SG_Connect()
        RF_amp = float(SG.query('POW:AMPL?'))
        print(f"RF Amplitude [dBm]: {RF_amp}")
        return RF_amp
    
    def set_rf_amplitude(self,value):
        SG = self.SG_Connect()
        SG.write('POW:AMPL {:.2f}'.format(value))
    
    
    def get_lf_toggle(self):
        """
        enable or disable low frequency output
        """
        SG = self.SG_Connect()
        return float(SG.query('LFO:STAT?'))

    
    def set_lf_toggle(self,value):
        SG = self.SG_Connect()
        SG.write('LFO:STAT {:s}'.format(value))
    
    
    def get_rf_toggle(self):
        """
        enable or disable RF output
        """
        SG = self.SG_Connect()
        OutputState = SG.query('OUTP:STAT?')
        print(f"RF output is in the following state: {OutputState}")
        return OutputState
    
    
    def set_rf_toggle(self,value):
        SG = self.SG_Connect()
        SG.write('OUTP:STAT {:s}'.format(value))
    
    
    def get_rf_frequency(self):
        """
        signal frequency
        units are in hertz
        """
        SG = self.SG_Connect()
        rf_freq = float(SG.query('FREQ?'))
        print(f"RF Frequency [GHz] is: {rf_freq*1e-9}")
        return rf_freq*1e-9
    
    
    def set_rf_frequency(self,value):
        SG = self.SG_Connect()
        SG.write('FREQ {:.2f}'.format(value))
    
    
    def get_lf_frequency(self):
        """
        signal frequency 0.5Hz-1MHz
        """
        SG = self.SG_Connect()
        return float(SG.query('LFO:FUNC:FREQ?'))
    
    
    def set_lf_frequency(self,value):
        SG = self.SG_Connect()
        SG.write('LFO:FUNC:FREQ {:.2f}'.format(value))
    
    #ALL EXCEPT MODEL UNR
    #@Feat(values={1,2})
    #def pll_loop_filter_mode(self):
    #    """
    #    sets PLL bandwidth to optimize phase noise
    #    1 optimizes below 10kHz, 2 optimizes above 10kHz
    #    """
    #    return float(self.query('FREQ:SYNT?'))
    #
    #@pll_loop_filter_mode.setter
    #def pll_loop_filter_mode(self,value):
    #    self.write('FREQ:SYNT {}'.format(value))
    
    
    def get_rf_offset(self): #not entirely sure if this is rf
        """
        RF offset
        units are dB
        """
        SG = self.SG_Connect()
        return float(SG.query('POW:OFFS?'))
    
    
    def set_rf_offset(self,value):
        SG = self.SG_Connect()
        SG.write('POW:OFFS {:.2f}'.format(value))
    
    
    def get_phase(self):
        """
        carrier phase
        from -Pi to Pi
        """
        SG = self.SG_Connect()
        return float(SG.query('PHAS?'))
    
    
    def set_phase(self,value):
        SG = self.SG_Connect()
        SG.write('PHAS {:.2f}'.format(value))
    
    
    def set_ref_phase(self):
        """
        sets current output phase as a zero reference
        """
        SG = self.SG_Connect()
        SG.write('PHAS:REF')

    
    def get_mod_toggle(self):
        """
        Modulation State
        """
        SG = self.SG_Connect()
        return float(SG.query('OUTP:MOD?'))
        
    
    def set_mod_toggle(self, value):
        SG = self.SG_Connect()
        SG.write('OUTP:MOD {}'.format(value))

#   ONLY WITH OPTION 002/602    
#    @Feat()
#    def mod_type(self):
#        """
#        Modulation State
#        """
#        return self.query('RAD:CUST:MOD:TYPE?')
#
#    @mod_type.setter
#    def mod_type(self, value):
#        self.write('RAD:CUST:MOD:TYPE {}'.format(value))