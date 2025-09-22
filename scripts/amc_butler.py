#!/usr/bin/env python
"""
Created on: 05/06/2025 11:16

Author: Shyam Bhuller, Alessandro Thea

Description: Check the status of an AMC or multiple AMCs to ensure they can be reached.
"""

import subprocess
import time
import sh
import re
import click
from rich import print

import tdemodules

def ping(host):
    return subprocess.call(['ping', "-c", '1', host]) == 0

class Commands():
    def __init__(self, controllers : dict):
        self.controllers = controllers

    def stop(self):
        for k, v in self.controllers.items():
            print(f"starting: {k}")
            v.card_stop()
        return

    def start(self):
        for k, v in self.controllers.items():
            print(f"starting: {k}")
            v.card_start()
        return

    def status(self):
        # Constantly get the status of the AMCs to check whether they can be accessed.
        if self.controllers:
            print("[yellow]Press ctrl-C to exit.[/yellow]")
            ti = 10
            t = time.time()
            while True:
                for k, v in self.controllers.items():
                    print(f"Reading status of AMC with IP: {k})")
                    v.card_status()
                print(f"[cyan]Sleeping {ti}s[/cyan]")
                time.sleep(ti)
                print(f"-- {time.time() - t:.2g} s elapsed")
        return






@click.command()
@click.argument('crate_ip', type=str)
@click.option('-a', '--amcs', type=int, multiple=True, default=[i for i in range(10)])
@click.option('-c', 'cmd',  type=click.Choice(['arping', 'status', 'start', 'stop']), default=None)
def main(crate_ip, amcs, cmd):

    # get list of amcs from the command arguments
    try:
        sh.ping(["-c", '1', crate_ip])
        print(f"[green]uTCA crate {crate_ip} is active[/green]")
    except sh.ErrorReturnCode as e:
        print(f"[red]Could not ping uTCA Crate at IP: {crate_ip}[/red]")
        exit(1)

    crate_subnet = crate_ip.rsplit(".", 1)[0]
    nic_ip = crate_subnet+'.129'

    amc_ips = { i: crate_subnet + f".{i + 1}" for i in amcs}

    if cmd=='arping':


        devices = {
            'crate': crate_ip,
            'nic': nic_ip
        }

        devices.update({f'AMC {amc}': amc_ip for amc, amc_ip in amc_ips.items()})

        

        from concurrent.futures import ThreadPoolExecutor, as_completed
        import subprocess as sp
        import sys

        failures = []
        MAX_WORKERS=10
        def arping(amc_ip):
            return sh.arping(["-c", '1', amc_ip])
        try:
    
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                futures = {pool.submit(arping, amc_ip):(amc, amc_ip) for amc, amc_ip in devices.items()}
                for fut in as_completed(futures):
                    amc, amc_ip = futures[fut]
                    try:
                        rc = fut.result()
                    except sp.TimeoutExpired:
                        print(f"[TIMEOUT] {amc}", file=sys.stderr)
                        failures.append((amc, "timeout"))
                        continue
                    except sh.ErrorReturnCode as e:
                        print(f"- [red]Could not arping device at IP: {amc_ip}[/red]")
                        continue
                    except Exception as ex:
                        print(f"[EXCEPTION] {amc}: {ex}", file=sys.stderr)
                        failures.append((amc, "exception"))
                        continue

                    match = re.search(r"Unicast reply from\s+([\d.]+)\s+\[([0-9A-Fa-f:]{17})\]", rc)
                    if match:
                        ipaddr, mac = match.group(1), match.group(2)
                    print(f"- [green]{amc} ({amc_ip}) responded to arping : mac {mac}[/green]")

            
        except KeyboardInterrupt:
            print("\nInterrupted. Shutting down workers…", file=sys.stderr)
            # ProcessPool will terminate on context exit
    else:
        controllers = { amc_ip:tdemodules.AMCController(amc_ip, 54321 + (i + 1)) for i,amc_ip in amc_ips.items() }
        print(controllers)
        cmds = Commands(controllers)
        getattr(cmds, cmd)()

    return

    return

if __name__ == "__main__":

    main()