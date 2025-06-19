"""
Created on: 18/06/2025 10:25

Author: Shyam Bhuller

Description: get the mac address by arping with a known ip.
"""

import argparse
import os
import subprocess

def get_mac(host : str, ip : str) -> str | None:

    cmd = f"ssh {os.environ['USER']}@{host} arping -f {ip} -w 1"
    out = subprocess.run(cmd, stdout = subprocess.PIPE, shell = True)

    mac = "00:00:00:00:00:00"
    for l in out.stdout.decode().splitlines():
        if "Unicast" in l:
            mac = l.split("[")[-1].split("]")[0].lower()
            break
    if mac == "00:00:00:00:00:00":
        print(f"Warning: mac address for ip {ip} from host {host} was not found")
    return mac

if __name__ == "__main__":
    parser = argparse.ArgumentParser("get the mac address by arping with a known ip.")
    parser.add_argument(dest = "ip", help = "ip address")
    parser.add_argument(dest = "host", default = "localhost", help = "host machine to ping from")
    args = parser.parse_args()
    print(get_mac(args.host, args.ip))
