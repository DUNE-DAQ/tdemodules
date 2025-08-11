# AMC Butler

The AMC Butler can be used to `start`, `stop` and get the `status` of a crate:

```
amc_butler.py -c <crate_ip> --command <command>
```

or multiple AMCs:

```
amc_butler.py -a <amc_ips> --command <command>
```

The `start` and `stop` command are issued once for each AMC sequentially, while the status command runs indefinately and get the status of the AMCs every 10 s.