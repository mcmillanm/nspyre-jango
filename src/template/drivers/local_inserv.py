#!/usr/bin/env python
"""
Start up an instrument server to host drivers. For the purposes of this demo,
it's assumed that this is running on the same system that will run experimental
code.
"""
from pathlib import Path
import logging

from nspyre import InstrumentServer
from nspyre import InstrumentGateway
from nspyre import nspyre_init_logger
from nspyre import serve_instrument_server_cli

_HERE = Path(__file__).parent

# log to the console as well as a file inside the logs folder
nspyre_init_logger(
    logging.INFO,
    log_path=_HERE / '../logs',
    log_path_level=logging.DEBUG,
    prefix='local_inserv',
    file_size=10_000_000,
)

with InstrumentServer() as local_inserv, InstrumentGateway(port=42067) as remote_gw:
    local_inserv.add('subs', _HERE / 'subsystems_driver.py', 'SubsystemsDriver', args=[local_inserv, remote_gw], local_args=True)
    local_inserv.add('daq', _HERE / 'nspyre_drivers' / 'ni' / 'daq.py', 'DAQ')
    local_inserv.add('odmr_driver', _HERE / 'fake_odmr_driver.py', 'FakeODMRInstrument')
    local_inserv.add('swabian', _HERE / 'nspyre_drivers' / 'swabian' / 'SwabianPS82.py', 'SwabianPulseStreamer82')
    local_inserv.add('e8527d', _HERE / 'nspyre_drivers' / 'agilent' / 'e8257d.py', 'AgilentE8257D')
    #local_inserv.add('tlb6725', _HERE / 'nspyre_drivers' / 'newfocus' / 'tlb6725.py', 'TLB6725')
    # run a CLI (command-line interface) that allows the user to enter
    # commands to control the server
    serve_instrument_server_cli(local_inserv)
