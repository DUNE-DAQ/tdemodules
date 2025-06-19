# Generating Configurations for NP02

To generate the configurations of the AMCs, one can use `tdemodules_gen.py` to create the detector connections, segment and session for the tde readout.

## Generating configurations
Run to generate the tde-testcrate configuration (default):

```[bash]
tdemodules_gen.py
```

Run to genetate the full np02 tde configuration:

```[bash]
tdemodules_gen.py -f tde
```

Note that the starting source ID (source ID of the first CRP) can be changed (defaults to 8)

```[bash]
tdemodules_gen.py -s <some-integer>
```

and the host for the dpdk receiver can also be changed (this will also be the host used for the readout application)

```[bash]
tdemodules_gen.py -d <np0x-server-name>
```

## What to do after
Once a configuration is generated, you will see three files made:
```
<detector-name>-det-connections.data.xml # move into hw/
<detector-name>.data.xml # move into segments/
<detector-name>-session.data.xml # move into sessions/
```

Once moved in the the appropriate directories in `ehn1-daqconfigs`, update the include paths in the three respective files.

Next, the ip and MAC addresses for the NICs need to be provided. This is found by checking the NICs registered on the server in LanDB. The pcie address can be inferred through lspci and searching for the device name:

```[bash]
lspci -vv -m | grep -Ew "Device:|NUMANode:"'
```

(note it is easier to use `get_pcie_map.py` from `performancetest` to do this)

Then, the isolated cpus need to be assigned as lcores. The isolated cpus can be found by doing:

```[bash]
sudo cat /sys/devices/system/cpu/isolated
```

to check for any errors in the configuration files, you can run

```[bash]
oks_dump --files-only <xml-file>
```