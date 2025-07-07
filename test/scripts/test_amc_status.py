#!/usr/bin/env python
"""
Created on: 05/06/2025 11:16

Author: Shyam Bhuller

Description: Check the status of an AMC or multiple AMCs to ensure they can be reached.
"""

import argparse
import subprocess
import time

import tdemodules

def ping(host):
    return subprocess.call(['ping', "-c", '1', host]) == 0

def main(args : argparse.Namespace):
    # get list of amcs from the command arguments
    controllers = {}
    if args.crate:
        if not ping(args.crate): # try pinging the crate #?also do this for the AMC option?
            print(f"Could not ping uTCA Crate at IP: {args.crate}")
            exit(1)

        for i in range(10):  # 10 is the maximum number of AMCs for any given crate currently for np02. Could have an actual mapping to create the correct amount of controllers 
            ip = args.crate.rsplit(".", 1)[0] + f".{i + 1}"
            port = 54321 + (i + 1)
            controllers[ip] = tdemodules.AMCController(ip, port)
    elif args.amc:
        for i in args.amc:
            num = int(i.split(".")[-1])
            controllers[i] = tdemodules.AMCController(i, 54321 + num)
    else:
        print("how did we get here?")
        exit(2)

    # Constantly get the status of the AMCs to check whether they can be accessed.
    if controllers:
        print("press ctrl-C to exit.")
        ti = 10
        t = time.time()
        while True:
            for k, v in controllers.items():
                print(f"Reading status of AMC with IP: {k})")
                v.card_status()
            time.sleep(ti)
            print(f"-- {time.time() - t:.2g} s elapsed")

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Check the status of an AMC or multiple AMCs to ensure they can be reached.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--crate", type = str, help = "IP address of crate MCH.")
    group.add_argument("-a", "--amc", type = str, nargs = "+", help = "IP address/es of AMCs.")
    args = parser.parse_args()
    print(args)
    main(args)