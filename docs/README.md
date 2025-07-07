# tdemodules

This pacakge provides DAQ modules for controlling the AMCs used to transmit data from the top drift cold electronics to the readout servers.

For instructions on first time initialization of the AMCs: [Initialize AMCs](docs/first_time_setup_amc.md)

Two test script exist:

- `test_amc_commands.py`: test the commands used to start readout, stop readout and get the status of the AMCs. enables data taking for 1 minute using the tde test crate.
- `test_amc_status.py`: check if a crate and/or the AMCs can be communicated with using the TFTP protocol from the AMCControllers.